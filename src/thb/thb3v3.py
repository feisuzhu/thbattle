# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, get_seed_for
from game.autoenv import user_input
from thb.actions import DrawCards, GenericAction, PlayerDeath, PlayerTurn, RevealIdentity
from thb.actions import action_eventhandlers
from thb.characters.baseclasses import mixin_character
from thb.common import PlayerIdentity, build_choices, roll
from thb.inputlets import ChooseGirlInputlet
from utils import BatchList, Enum


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

        g = Game.getgame()

        # see if game ended
        force1, force2 = g.forces
        tgt = act.target
        dead = lambda p: p.dead or p.dropped or p is tgt

        if all(dead(p) for p in force1):
            g.winners = force2[:]
            g.game_end()

        if all(dead(p) for p in force2):
            g.winners = force1[:]
            g.game_end()

        return act


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = Game.getgame()
        params = self.params

        from thb.cards import Deck

        g.deck = Deck(ppoints=(1, 1, 1, 1, 1))
        g.ehclasses = []

        if params['random_seat']:
            seed = get_seed_for(g.players)
            random.Random(seed).shuffle(g.players)
            g.emit_event('reseat', None)

        for i, p in enumerate(g.players):
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        g.forces = forces = BatchList([BatchList(), BatchList()])
        for i, p in enumerate(g.players):
            f = i % 2
            p.force = f
            forces[f].append(p)

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        from . import characters
        chars = characters.get_characters('common', '3v3')
        choices, imperial_choices = build_choices(
            g, self.items,
            candidates=chars, players=g.players,
            num=16, akaris=4, shared=True,
        )

        roll_rst = roll(g, self.items)
        first = roll_rst[0]
        first_index = g.players.index(first)

        order_list   = (0, 5, 3, 4, 2, 1)
        n = len(order_list)
        order = [g.players[(first_index + i) % n] for i in order_list]

        akaris = []
        with InputTransaction('ChooseGirl', g.players, mapping=choices) as trans:
            chosen = set()

            for p, c in imperial_choices:
                chosen.add(p)
                c.chosen = p
                g.set_character(p, c.char_cls)
                trans.notify('girl_chosen', (p, c))

            for p in order:
                if p in chosen:
                    continue

                c = user_input([p], ChooseGirlInputlet(g, choices), timeout=30, trans=trans)
                c = c or [_c for _c in choices[p] if not _c.chosen][0]
                c.chosen = p

                if c.akari:
                    c.akari = False
                    akaris.append((p, c))
                else:
                    g.set_character(p, c.char_cls)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris
        if akaris:
            g.players.reveal([i[1] for i in akaris])

            for p, c in akaris:
                g.set_character(p, c.char_cls)

        # -------
        for p in g.players:
            log.info(
                u'>> Player: %s:%s %s',
                p.__class__.__name__,
                Identity.TYPE.rlookup(p.identity.type),
                p.account.username,
            )
        # -------

        first = g.players[first_index]

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DrawCards(p, amount=3 if p is first else 4))

        pl = g.players.rotate_to(first)

        for i, p in enumerate(cycle(pl)):
            if i >= 6000: break
            if not p.dead:
                g.emit_event('player_turn', p)
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        return True


class THBattle(Game):
    n_persons    = 6
    game_ehs     = _game_ehs
    bootstrap    = THBattleBootstrap
    params_def   = {
        'random_seat': (False, True),
    }

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def set_character(g, p, cls):
        # mix char class with player -->
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)
        g.forces[0].replace(p, new)
        g.forces[1].replace(p, new)
        assert not old_cls
        ehs = g.ehclasses
        ehs.extend(cls.eventhandlers_required)
        g.update_event_handlers()
        g.emit_event('switch_character', (p, new))
        return new

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.set_event_handlers(EventHandler.make_list(ehclasses))

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
        return [{'event': 'pick', 'attributes': {
            'character': p.__class__.__name__,
            'gamemode': g.__class__.__name__,
            'identity': '-',
            'victory': p in g.winners,
        }} for p in g.players]
