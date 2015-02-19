# -*- coding: utf-8 -*-
import random
from itertools import cycle
from collections import defaultdict
import logging
import settings

from utils import Enum, filter_out

from game.autoenv import Game, EventHandler, InterruptActionFlow, InputTransaction, user_input
from game import sync_primitive

from .common import PlayerIdentity, CharChoice, get_seed_for

from .actions import DeadDropCards, PlayerTurn, DistributeCards, RevealIdentity
from .actions import action_eventhandlers

from .characters.baseclasses import mixin_character

from .inputlets import ChooseGirlInputlet, SortCharacterInputlet

log = logging.getLogger('THBattle')
_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    interested = (
        ('action_before', DeadDropCards),
    )

    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, DeadDropCards): return act
        tgt = act.target

        g = Game.getgame()

        if not tgt.characters:
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
    interested = (
        ('action_before', PlayerTurn),
        ('action_after', PlayerTurn),
        'action_stage_action',
    )

    def handle(self, evt_type, act):
        cond = evt_type in ('action_before', 'action_after')
        cond = cond and isinstance(act, PlayerTurn)
        cond = cond or evt_type == 'action_stage_action'
        cond and self.do_switch()
        return act

    @staticmethod
    def do_switch():
        g = Game.getgame()

        for p in [p for p in g.players if p.dead and p.characters]:
            new = g.next_character(p)
            g.process_action(DistributeCards(new, 4))


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleKOF(Game):
    n_persons  = 2
    game_ehs   = _game_ehs
    params_def = {
        'no_imba': (True, False),
    }

    def game_start(g, params):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = []

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        # choose girls -->
        from characters import get_characters
        chars = get_characters('kof' if params['no_imba'] else 'kofall')

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

        for p in g.players:
            seed = get_seed_for(p)
            random.Random(seed).shuffle(p.choices)

        mapping = {first: first.choices, second: second.choices}
        rst = user_input(g.players, SortCharacterInputlet(g, mapping, 3), timeout=30, type='all')

        for p in g.players:
            perm = p.choices
            perm = [   # weird snap for debug
                perm[i]
                for i in
                rst[p]
                [:3]
            ]
            p.characters = [c.char_cls for c in perm]
            del p.choices

        first = g.next_character(first)
        second = g.next_character(second)

        order = [0, 1] if first is g.players[0] else [1, 0]

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        g.emit_event('game_begin', g)

        for p in pl:
            g.process_action(DistributeCards(p, amount=3 if p is first else 4))

        for i, idx in enumerate(cycle(order)):
            p = g.players[idx]
            if i >= 6000: break
            if p.dead:
                assert p.characters  # if not holds true, DeathHandler should end game.
                KOFCharacterSwitchHandler.do_switch()
                p = g.players[idx]  # player changed

            assert not p.dead

            try:
                g.emit_event('player_turn', p)
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass

    def can_leave(g, p):
        return False

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.event_handlers = EventHandler.make_list(ehclasses)

    def next_character(g, p):
        assert p.characters
        char = CharChoice(p.characters.pop(0))
        g.players.reveal(char)
        cls = char.char_cls

        # mix char class with player -->
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)

        ehs = g.ehclasses
        ehs.extend(cls.eventhandlers_required)
        g.update_event_handlers()

        g.emit_event('switch_character', new)

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
