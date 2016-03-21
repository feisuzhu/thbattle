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
from thb.actions import DistributeCards, DrawCards, DropCards, GenericAction, PlayerDeath
from thb.actions import PlayerTurn, RevealIdentity, action_eventhandlers
from thb.characters.baseclasses import mixin_character
from thb.common import PlayerIdentity, build_choices, sync_primitive
from thb.inputlets import ChooseGirlInputlet
from utils import Enum


# -- code --
log = logging.getLogger('THBattleIdentity')
_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class IdentityRevealHandler(EventHandler):
    interested = ('action_apply', )
    execute_before = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()
            tgt = act.target

            g.process_action(RevealIdentity(tgt, g.players))

        return act


@game_eh
class DeathHandler(EventHandler):
    interested = ('action_apply', 'action_after')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()
            T = Identity.TYPE

            tgt = act.target
            dead = lambda p: p.dead or p is tgt

            # curtain's win
            survivors = [p for p in g.players if not dead(p)]
            if len(survivors) == 1:
                pl = g.players
                pl.reveal([p.identity for p in g.players])

                if survivors[0].identity.type == T.CURTAIN:
                    g.winners = survivors[:]
                    g.game_end()

            deads = defaultdict(list)
            for p in g.players:
                if dead(p):
                    deads[p.identity.type].append(p)

            def winner(*identities):
                pl = g.players
                pl.reveal([p.identity for p in g.players])

                g.winners = [p for p in pl if p.identity.type in identities]
                g.game_end()

            def no(identity):
                return len(deads[identity]) == g.identities.count(identity)

            # attackers' & curtain's win
            if len(deads[T.BOSS]):
                if g.double_curtain:
                    winner(T.ATTACKER)
                else:
                    if no(T.ATTACKER):
                        winner(T.CURTAIN)
                    else:
                        winner(T.ATTACKER)

            # boss & accomplices' win
            if no(T.ATTACKER) and no(T.CURTAIN):
                winner(T.BOSS, T.ACCOMPLICE)

            # all survivors dropped
            if all([p.dropped for p in survivors]):
                pl = g.players
                pl.reveal([p.identity for p in pl])
                g.winners = []
                g.game_end()

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            T = Identity.TYPE
            g = Game.getgame()
            tgt = act.target
            src = act.source

            if src:
                if tgt.identity.type == T.ATTACKER:
                    g.process_action(DrawCards(src, 3))
                elif tgt.identity.type == T.ACCOMPLICE:
                    if src.identity.type == T.BOSS:
                        g.players.exclude(src).reveal(list(src.cards))

                        cards = []
                        cards.extend(src.cards)
                        cards.extend(src.showncards)
                        cards.extend(src.equips)
                        cards and g.process_action(DropCards(src, src, cards))

        return act


class Identity(PlayerIdentity):
    # 城管 BOSS 道中 黑幕
    class TYPE(Enum):
        HIDDEN = 0
        ATTACKER = 1
        BOSS = 4
        ACCOMPLICE = 2
        CURTAIN = 3


class THBattleIdentityBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = Game.getgame()
        params = self.params

        from thb.cards import Deck

        g.deck = Deck(ppoints=(1, 1, 1, 1, 1, 1, 2, 2))
        g.ehclasses = []

        g.double_curtain = params['double_curtain']

        if g.double_curtain:
            g.identities = g.identities[1:] + g.identities[-1:]

        # choose girls init -->
        from .characters import get_characters
        chars = get_characters('id', 'id8')

        # choose boss
        idx = sync_primitive(g.random.randrange(len(g.players)), g.players)
        boss = g.boss = g.players[idx]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS

        g.process_action(RevealIdentity(boss, g.players))

        pl = g.players.rotate_to(boss)

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=[boss],
            num=[5], akaris=[1],
            shared=False,
        )

        with InputTransaction('ChooseGirl', [boss], mapping=choices) as trans:
            c = user_input([boss], ChooseGirlInputlet(g, choices), 30, 'single', trans)

            c = c or choices[boss][-1]
            c.chosen = boss
            c.akari = False
            g.players.reveal(c)
            trans.notify('girl_chosen', (boss, c))

        try:
            chars.remove(c.char_cls)
        except:
            pass

        # mix it in advance
        # so the others could see it

        boss = g.switch_character(boss, c.char_cls)

        # boss's hp bonus
        if g.n_persons > 5:
            boss.maxlife += 1

        boss.life = boss.maxlife

        # reseat
        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(g.players)
        g.emit_event('reseat', None)

        # tell the others their own identity
        il = list(g.identities)
        g.random.shuffle(il)
        for p in g.players.exclude(boss):
            p.identity = Identity()
            id = il.pop()
            if Game.SERVER_SIDE:
                p.identity.type = id
            g.process_action(RevealIdentity(p, p))

        # others choose girls
        pl = g.players.exclude(boss)

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=pl,
            num=[4] * len(pl), akaris=[1] * len(pl),
            shared=False,
        )

        with InputTransaction('ChooseGirl', pl, mapping=choices) as trans:
            ilet = ChooseGirlInputlet(g, choices)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            result = user_input(pl, ilet, type='all', trans=trans)

        # mix char class with player -->
        for p in pl:
            c = result[p] or choices[p][-1]
            c.akari = False
            g.players.reveal(c)
            p = g.switch_character(p, c.char_cls)

        # -------
        for p in g.players:
            log.info(
                u'>> Player: %s:%s %s',
                p.__class__.__name__,
                Identity.TYPE.rlookup(p.identity.type),
                p.account.username,
            )
        # -------

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=4))

        for i, p in enumerate(cycle(g.players.rotate_to(boss))):
            if i >= 6000: break
            if not p.dead:
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        return True


class THBattleIdentity(Game):
    n_persons = 8
    game_ehs = _game_ehs
    bootstrap = THBattleIdentityBootstrap
    params_def = {
        'double_curtain': (False, True),
    }
    T = Identity.TYPE
    identities = [
        T.ATTACKER, T.ATTACKER, T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE, T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def switch_character(g, p, cls):
        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)

        ehs = g.ehclasses
        assert not oldcls
        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()
        g.emit_event('switch_character', (old, p))

        return p

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.set_event_handlers(EventHandler.make_list(ehclasses))

    def decorate(self, p):
        from thb.cards import CardList
        p.cards          = CardList(p, 'cards')        # Cards in hand
        p.showncards     = CardList(p, 'showncards')   # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')       # Equipments
        p.fatetell       = CardList(p, 'fatetell')     # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')      # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]  # cardlists should shown to others
        p.tags           = defaultdict(int)

    def get_stats(g):
        return [{'event': 'pick', 'attributes': {
            'character': p.__class__.__name__,
            'gamemode': g.__class__.__name__,
            'identity': Identity.TYPE.rlookup(p.identity.type),
            'victory': p in g.winners,
        }} for p in g.players]
