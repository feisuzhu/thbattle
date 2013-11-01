# -*- coding: utf-8 -*-
import random
from game.autoenv import Game, EventHandler, GameEnded, InterruptActionFlow, user_input, InputTransaction

from .actions import PlayerTurn, PlayerDeath, DrawCards, DropCards, RevealIdentity
from .actions import action_eventhandlers
from .characters.baseclasses import mixin_character

from itertools import cycle
from collections import defaultdict

from .common import PlayerIdentity, sync_primitive, CharChoice, get_seed_for
from .inputlets import ChooseGirlInputlet

import logging
log = logging.getLogger('THBattleIdentity')
_game_ehs = {}
_game_actions = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


def game_action(cls):
    _game_actions[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target
        g = Game.getgame()

        g.process_action(RevealIdentity(tgt, g.players))

        if act.source:
            src = act.source
            if tgt.identity.type == Identity.TYPE.ATTACKER:
                g.process_action(DrawCards(src, 3))
            elif tgt.identity.type == Identity.TYPE.ACCOMPLICE:
                if src.identity.type == Identity.TYPE.BOSS:
                    if src.cards:
                        g.players.exclude(src).reveal(list(src.cards))
                        g.process_action(DropCards(src, src.cards))
                    if src.showncards: g.process_action(DropCards(src, src.showncards))
                    if src.equips: g.process_action(DropCards(src, src.equips))

        # see if game ended
        T = Identity.TYPE

        def build():
            deads = defaultdict(list)
            for p in g.players:
                if p.dead:
                    deads[p.identity.type].append(p)
            return deads

        # curtain's win
        survivors = [p for p in g.players if not p.dead]
        if len(survivors) == 1:
            pl = g.players
            pl.reveal([p.identity for p in g.players])

            if survivors[0].identity.type == T.CURTAIN:
                g.winners = survivors[:]
                raise GameEnded

        deads = build()

        # boss & accomplices' win
        if len(deads[T.ATTACKER]) == g.identities.count(T.ATTACKER):
            if len(deads[T.CURTAIN]) == g.identities.count(T.CURTAIN):
                pl = g.players
                pl.reveal([p.identity for p in g.players])

                g.winners = [p for p in pl if p.identity.type in (T.BOSS, T.ACCOMPLICE)]
                raise GameEnded

        # attackers' win
        if len(deads[T.BOSS]):
            pl = g.players
            pl.reveal([p.identity for p in g.players])

            g.winners = [p for p in pl if p.identity.type == T.ATTACKER]
            raise GameEnded

        return act


class Identity(PlayerIdentity):
    # 城管 BOSS 道中 黑幕
    class TYPE:
        HIDDEN = 0
        ATTACKER = 1
        BOSS = 2
        ACCOMPLICE = 3
        CURTAIN = 4


class THBattleIdentity(Game):
    n_persons = 8
    game_actions = _game_actions
    T = Identity.TYPE
    identities = [
        T.ATTACKER, T.ATTACKER, T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE, T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T

    def game_start(g):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = ehclasses = list(action_eventhandlers) + _game_ehs.values()

        # choose girls init -->
        from .characters import characters as chars
        from .characters.akari import Akari

        chars = list(chars)
        if Game.CLIENT_SIDE:
            chars = [None] * len(chars)

        g.random.shuffle(chars)

        # choose boss
        idx = sync_primitive(g.random.randrange(len(g.players)), g.players)
        boss = g.boss = g.players[idx]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS

        g.process_action(RevealIdentity(boss, g.players))

        boss.choices = [CharChoice(c) for c in chars[:4]]
        boss.choices.append(CharChoice(Akari))
        del chars[:4]

        for p in g.players.exclude(boss):
            p.choices = [CharChoice(c) for c in chars[:3]]
            p.choices.append(CharChoice(Akari))
            del chars[:3]

        for p in g.players:
            p.reveal(p.choices)

        mapping = {boss: boss.choices}
        with InputTransaction('ChooseGirl', [boss], mapping=mapping) as trans:
            c = user_input([boss], ChooseGirlInputlet(g, mapping), 30, 'single', trans)

            c = c or boss.choices[-1]
            c.chosen = boss
            g.players.reveal(c)
            trans.notify('girl_chosen', c)

            if c.char_cls is Akari:
                c = CharChoice(chars.pop())
                g.players.reveal(c)

            # mix it in advance
            # so the others could see it

            boss = g.switch_character(boss, c.char_cls)

            # boss's hp bonus
            if len(g.players) > 5:
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

        pl = g.players.exclude(boss)
        mapping = {p: p.choices for p in pl}  # CAUTION, DICT HERE
        with InputTransaction('ChooseGirl', pl, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', rst) or rst)
            result = user_input(pl, ilet, type='all', trans=trans)

        # not enough chars for random, reuse unselected
        for p in pl:
            if result[p]: result[p].chosen = p
            chars.extend([i.char_cls for i in p.choices if not i.chosen and i.char_cls is not Akari])

        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(chars)

        # mix char class with player -->
        for p in pl:
            c = result[p]
            c = c or p.choices[-1]
            g.players.reveal(c)

            if c.char_cls is Akari:
                c = CharChoice(chars.pop())
                g.players.reveal(c)

            p = g.switch_character(p, c.char_cls)

        g.event_handlers = EventHandler.make_list(ehclasses)

        g.emit_event('game_begin', g)

        try:
            for p in g.players:
                g.process_action(DrawCards(p, amount=4))

            pl = g.players.rotate_to(boss)

            for i, p in enumerate(cycle(pl)):
                if i >= 6000: break
                if not p.dead:
                    try:
                        g.process_action(PlayerTurn(p))
                    except InterruptActionFlow:
                        pass

        except GameEnded:
            pass

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
        g.emit_event('switch_character', p)

        return p

    def decorate(self, p):
        from cards import CardList
        p.cards = CardList(p, 'cards')  # Cards in hand
        p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips = CardList(p, 'equips')  # Equipments
        p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
        p.special = CardList(p, 'special')  # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]  # cardlists should shown to others
        p.tags = defaultdict(int)


class THBattleIdentity5(THBattleIdentity):
    n_persons = 5
    T = Identity.TYPE

    identities = [
        T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T
