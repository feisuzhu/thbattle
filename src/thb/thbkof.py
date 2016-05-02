# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, list_shuffle
from game.autoenv import user_input
from thb.actions import DistributeCards, GenericAction, PlayerDeath, PlayerTurn, RevealIdentity
from thb.actions import action_eventhandlers
from thb.characters.baseclasses import Character, mixin_character
from thb.common import PlayerIdentity, build_choices, roll
from thb.inputlets import ChooseGirlInputlet
from utils import Enum, first


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

        if tgt.remaining[0] <= 0:
            pl = g.players[:]
            pl.remove(tgt)
            g.winners = pl
            g.game_end()

        tgt.remaining[0] -= 1

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
        cond and self.do_switch_dead()
        return act

    @classmethod
    def do_switch_dead(cls):
        g = Game.getgame()

        for p in [p for p in g.players if p.dead and p.choices]:
            new = cls.switch(p)
            g.process_action(DistributeCards(new, 4))
            g.emit_event('character_debut', (p, new))

    @staticmethod
    def switch(p):
        g = Game.getgame()
        mapping = {p: p.choices}

        with InputTransaction('ChooseGirl', [p], mapping=mapping) as trans:
            rst = user_input([p], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
            rst = rst or p.choices[0]

        p = g.next_character(p, rst)
        p.choices.remove(rst)
        return p


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleKOFBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = Game.getgame()

        from . import cards

        g.pick_history = []

        g.deck = cards.Deck(cards.kof_card_definition, ppoints=(1,))
        g.ehclasses = []
        g.current_player = None

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        # choose girls -->
        from thb.characters import get_characters
        chars = get_characters('common', 'kof')

        A, B = roll(g, self.items)
        order = [A, B, B, A, A, B, B, A, A, B]

        choices, imperial_choices = build_choices(
            g, self.items,
            candidates=chars, players=[A, B],
            num=10, akaris=4, shared=True,
        )

        chosen = {A: [], B: []}

        with InputTransaction('ChooseGirl', g.players, mapping=choices) as trans:
            for p, c in imperial_choices:
                c.chosen = p
                chosen[p].append(c)
                trans.notify('girl_chosen', (p, c))
                order.remove(p)

            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, choices), 10, 'single', trans)
                c = c or first(choices[p], lambda c: not c.chosen)

                c.chosen = p
                chosen[p].append(c)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris for themselves
        for p in [A, B]:
            for c in chosen[p]:
                c.akari = False
                p.reveal(c)
                del c.chosen

        list_shuffle(chosen[A], A)
        list_shuffle(chosen[B], B)

        with InputTransaction('ChooseGirl', g.players, mapping=chosen) as trans:
            ilet = ChooseGirlInputlet(g, chosen)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            rst = user_input([A, B], ilet, type='all', trans=trans)

        def s(p):
            c = rst[p] or chosen[p][0]
            chosen[p].remove(c)
            p.choices = chosen[p]
            p.remaining = [2]
            p = g.next_character(p, c)
            return p

        A, B = s(A), s(B)

        order = [1, 0] if A is g.players[0] else [0, 1]

        for p in [A, B]:
            g.process_action(RevealIdentity(p, g.players))

        g.emit_event('game_begin', g)

        g.process_action(DistributeCards(A, amount=4))
        g.process_action(DistributeCards(B, amount=3))

        for i in order:
            g.emit_event('character_debut', (None, g.players[i]))

        for i, idx in enumerate(cycle(order)):
            p = g.players[idx]
            if i >= 6000: break
            if p.dead:
                KOFCharacterSwitchHandler.do_switch_dead()
                p = g.players[idx]  # player changed

            assert not p.dead

            try:
                g.emit_event('player_turn', p)
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass


class THBattleKOF(Game):
    n_persons  = 2
    game_ehs   = _game_ehs
    bootstrap  = THBattleKOFBootstrap
    params_def = {}

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

        p.cards          = CardList(p, 'cards')       # Cards in hand
        p.showncards     = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')      # Equipments
        p.fatetell       = CardList(p, 'fatetell')    # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')     # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags           = defaultdict(int)

    def get_stats(g):
        to_p = lambda p: p.player if isinstance(p, Character) else p
        return [{'event': 'pick', 'attributes': {
            'character': p.__class__.__name__,
            'gamemode': g.__class__.__name__,
            'identity': '-',
            'victory': to_p(p) is g.winners[0].player,
        }} for p in g.pick_history]
