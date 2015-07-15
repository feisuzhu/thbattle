# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging

# -- third party --
# -- own --
from game import sync_primitive
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, list_shuffle
from game.autoenv import user_input
from gamepack.thb.actions import DistributeCards, PlayerDeath, PlayerTurn, RevealIdentity
from gamepack.thb.actions import action_eventhandlers
from gamepack.thb.characters.baseclasses import Character, mixin_character
from gamepack.thb.common import CharChoice, PlayerIdentity
from gamepack.thb.inputlets import ChooseGirlInputlet
from utils import Enum, filter_out
import settings


# -- code --
log = logging.getLogger('THBattle')
_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target

        g = Game.getgame()

        if len(tgt.choices) <= 2:
            pl = g.players[:]
            pl.remove(tgt)
            g.winners = pl
            g.game_end()

        pl = g.players
        if pl[0].dropped:
            g.winners = [pl[1]]
            g.game_end()

        if pl[1].dropped:
            g.winners = [pl[0]]
            g.game_end()

        return act


@game_eh
class KOFCharacterSwitchHandler(EventHandler):
    interested = ('action_after', 'action_before', 'action_stage_action')

    def handle(self, evt_type, act):
        cond = evt_type in ('action_before', 'action_after')
        cond = cond and isinstance(act, PlayerTurn)
        cond = cond or evt_type == 'action_stage_action'
        cond and self.do_switch()
        return act

    @staticmethod
    def do_switch():
        g = Game.getgame()

        for p in [p for p in g.players if p.dead and p.choices]:
            mapping = {p: p.choices}

            with InputTransaction('ChooseGirl', [p], mapping=mapping) as trans:
                rst = user_input([p], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                rst = rst or p.choices[0]

            old = p
            p = g.next_character(p, rst)
            p.choices.remove(rst)

            g.process_action(DistributeCards(p, 4))
            g.emit_event('character_debut', (old, p))


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleKOF(Game):
    n_persons  = 2
    game_ehs   = _game_ehs
    params_def = {}

    def game_start(g, params):
        # game started, init state
        from . import cards

        g.pick_history = []

        g.deck = cards.Deck(cards.kof_card_definition)
        g.ehclasses = []
        g.current_turn = None

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        # choose girls -->
        from characters import get_characters
        chars = get_characters('kof')

        testing = list(settings.TESTING_CHARACTERS)
        testing = filter_out(chars, lambda c: c.__name__ in testing)

        _chars = g.random.sample(chars, 10)
        _chars.extend(testing)

        from characters.akari import Akari
        if Game.SERVER_SIDE:
            choice = [CharChoice(cls) for cls in _chars[-10:]]

            for c in g.random.sample(choice, 4):
                c.real_cls = c.char_cls
                c.char_cls = Akari

        elif Game.CLIENT_SIDE:
            choice = [CharChoice(None) for i in xrange(10)]

        # -----------

        g.players.reveal(choice)

        # roll
        roll = range(len(g.players))
        g.random.shuffle(roll)
        pl = g.players
        roll = sync_primitive(roll, pl)

        roll = [pl[i] for i in roll]

        g.emit_event('game_roll', roll)

        first = roll[0]
        second = roll[1]

        g.emit_event('game_roll_result', first)
        # ----

        # akaris = {}  # DO NOT USE DICT! THEY ARE UNORDERED!
        akaris = []

        A, B = first, second
        order = [A, B, B, A, A, B, B, A, A, B]
        A.choices = []
        B.choices = []
        choice_mapping = {A: choice, B: choice}
        del A, B

        with InputTransaction('ChooseGirl', g.players, mapping=choice_mapping) as trans:
            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, choice_mapping), 10, 'single', trans)
                if not c:
                    # first non-chosen char
                    for c in choice:
                        if not c.chosen:
                            c.chosen = p
                            break

                if issubclass(c.char_cls, Akari):
                    akaris.append((p, c))

                c.chosen = p
                p.choices.append(c)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris for themselves
        for p, c in akaris:
            c.char_cls = c.real_cls
            p.reveal(c)

        for c in choice:
            del c.chosen

        list_shuffle(first.choices, first)
        list_shuffle(second.choices, second)

        mapping = {first: first.choices, second: second.choices}

        with InputTransaction('ChooseGirl', g.players, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            rst = user_input(pl, ilet, type='all', trans=trans)

        def s(p):
            c = rst[p] or p.choices[0]
            p = g.next_character(p, c)
            p.choices.remove(c)
            return p

        first, second = s(first), s(second)

        order = [1, 0] if first is g.players[0] else [0, 1]

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        g.emit_event('game_begin', g)

        for p in pl:
            g.process_action(DistributeCards(p, amount=4 if p is first else 3))

        for i in order:
            g.emit_event('character_debut', (None, g.players[i]))

        for i, idx in enumerate(cycle(order)):
            p = g.players[idx]
            if i >= 6000: break
            if p.dead:
                KOFCharacterSwitchHandler.do_switch()
                p = g.players[idx]  # player changed

            assert not p.dead

            try:
                g.emit_event('player_turn', p)
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass

    def get_opponent(g, p):
        a, b = g.players
        if p is a:
            return b
        elif p is b:
            return a
        else:
            raise Exception('WTF?!')

    def can_leave(g, p):
        return False

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.set_event_handlers(EventHandler.make_list(ehclasses))

    def next_character(g, p, choice):
        g.players.reveal(choice)
        cls = choice.char_cls

        # mix char class with player -->
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)

        ehs = g.ehclasses
        ehs.extend(cls.eventhandlers_required)
        g.update_event_handlers()

        g.emit_event('switch_character', (p, new))

        g.pick_history.append([cls, p])

        return new

    def decorate(g, p):
        from .cards import CardList
        from .characters.baseclasses import Character
        assert isinstance(p, Character)

        p.cards = CardList(p, 'cards')  # Cards in hand
        p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips = CardList(p, 'equips')  # Equipments
        p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
        p.special = CardList(p, 'special')  # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags = defaultdict(int)

    def get_stats(g):
        to_p = lambda p: p.player if isinstance(p, Character) else p
        return [{'event': 'pick', 'attributes': {
            'character': p.__class__.__name__,
            'gamemode': g.__class__.__name__,
            'identity': '-',
            'victory': to_p(p) is g.winners[0].player,
        }} for p in g.pick_history]
