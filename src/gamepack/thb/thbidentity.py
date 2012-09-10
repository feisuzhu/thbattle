# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList

from actions import *
from itertools import cycle
from collections import defaultdict
import random

from utils import BatchList, check, CheckFailed

from .common import *

import logging
log = logging.getLogger('THBattleIdentity')

_game_ehs = {}
def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls

_game_actions = {}
def game_action(cls):
    _game_actions[cls.__name__] = cls
    return cls

from thb3v3 import PlayerDeath, TryRevive
game_action(PlayerDeath)
game_action(TryRevive)

@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.life > 0: return act
            g = Game.getgame()
            if not g.process_action(TryRevive(tgt, dmgact=act)):
                g.process_action(PlayerDeath(act.source, tgt))
                from .actions import RevealIdentity, DrawCards, DropCards
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
                if len([p for p in g.players if p.dead]) == len(g.players) - 1:
                    pl = g.players
                    pl.reveal([p.identity for p in g.players])

                    deads = build()
                    if not deads[T.CURTAIN]:
                        g.winners = [p for p in pl if p.identity.type == T.CURTAIN]
                        raise GameEnded

                deads = build()

                # boss & accomplices' win
                if len(deads[T.ATTACKER]) == g.identities.count(T.ATTACKER):
                    if deads[T.CURTAIN]:
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
        from cards import Card, Deck, CardList

        g.deck = Deck()

        ehclasses = list(action_eventhandlers) + _game_ehs.values()

        np = g.n_persons

        for p in g.players:
            p.cards = CardList(p, CardList.HANDCARD) # Cards in hand
            p.showncards = CardList(p, CardList.SHOWNCARD) # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, CardList.EQUIPS) # Equipments
            p.fatetell = CardList(p, CardList.FATETELL) # Cards in the Fatetell Zone
            p.special = CardList(p, CardList.SPECIAL) # used on special purpose

            p.showncardlists = [p.showncards] # cardlists should shown to others

            p.tags = defaultdict(int)

            p.dead = False
            p.need_shuffle = False

        # choose girls init -->
        from characters import characters as chars

        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(random.sample(chars, 3*np+2), xrange(3*np+2))
            ]
        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(3*np+2)
            ]

        chosen_girls = []
        pl = PlayerList(g.players)
        def process(p, cid):
            try:
                retry = p._retry
            except AttributeError:
                retry = 3

            retry -= 1
            try:
                check(isinstance(cid, int))
                i = p._choose_tag
                if p is boss:
                    assert p is pl[-1]
                    check(i*3 <= cid< (i+1)*3+2)
                else:
                    check(i*3 <= cid < (i+1)*3)
                c = choice[cid]
                if c.chosen and retry > 0:
                    p._retry = retry
                    raise ValueError
                c.chosen = p
                chosen_girls.append(c)
                g.emit_event('girl_chosen', c)
                pl.remove(p)
                return c

            except CheckFailed as e:
                return None

            finally:
                try:
                    del p._retry
                    del p._choose_tag
                except AttributeError:
                    pass

        # choose boss
        idx = sync_primitive(random.randrange(len(g.players)), g.players)
        pl[-1], pl[idx] = pl[idx], pl[-1]
        boss = g.boss = pl[-1]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS

        g.process_action(RevealIdentity(boss, g.players))

        for i, p in enumerate(pl):
            p._choose_tag = i
            p.reveal(choice[i*3:(i+1)*3])

        boss.reveal(choice[-2:])

        PlayerList([boss]).user_input_all('choose_girl', process, choice, timeout=30)
        if not chosen_girls:
            # didn't choose
            offs = sync_primitive(random.randrange(5), g.players)
            c = choice[(len(pl)-1)*3+offs]
            c.chosen = boss
            g.emit_event('girl_chosen', c)
            pl.remove(boss)
        else:
            c = chosen_girls.pop()

        assert c.chosen is boss

        g.players.reveal(c)

        # mix it in advance
        # so the others could see it

        mixin_character(boss, c.char_cls)
        boss.skills = boss.skills[:] # make it instance variable
        ehclasses.extend(boss.eventhandlers_required)

        # boss's hp bonus
        if len(g.players) > 5:
            boss.maxlife += 1

        g.emit_event('boss_chosen', boss)

        # reseat
        opl = g.players
        loc = range(len(opl))
        random.shuffle(loc)
        loc = sync_primitive(loc, opl)
        npl = opl[:]
        for i, l in zip(range(len(opl)), loc):
            npl[i] = opl[l]
        g.players[:] = npl

        g.emit_event('reseat', None)

        # tell the others their own identity
        il = g.identities[:]
        random.shuffle(il)
        for p in g.players.exclude(boss):
            p.identity = Identity()
            id = il.pop()
            if Game.SERVER_SIDE:
                p.identity.type = id
            g.process_action(RevealIdentity(p, p))

        g.players.exclude(boss).user_input_all('choose_girl', process, choice, timeout=30) # ALL?? NOT ANY?!!

        # now you can have them all.
        g.players.reveal(choice)

        # if there's any person didn't make a choice -->
        # FIXME: this can choose girl from the other force!
        if pl:
            choice = [c for c in choice if not c.chosen]
            sample = sync_primitive(
                random.sample(xrange(len(choice)), len(pl)), g.players
            )
            for p, i in zip(pl, sample):
                c = choice[i]
                c.chosen = p
                chosen_girls.append(c)
                g.emit_event('girl_chosen', c)

        # mix char class with player -->
        for c in chosen_girls:
            p = c.chosen
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:] # make it instance variable
            ehclasses.extend(p.eventhandlers_required)

        # this will make UIEventHook the last one
        # BUT WHY? FORGOT BUT THIS CAUSES PROBLEMS, REVERT
        # PROBLEM:
        # Reject prompt string should appear when the action fired,
        # actually appears after the whole reject process finished,
        # IN REVERSE ORDER.
        #g.event_handlers[:] = EventHandler.make_list(ehclasses) + g.event_handlers
        g.event_handlers.extend(EventHandler.make_list(ehclasses))

        for p in g.players:
            p.life = p.maxlife

        g.emit_event('game_begin', g)

        try:
            for p in g.players:
                g.process_action(DrawCards(p, amount=4))

            pl = g.players.rotate_to(boss)

            for i, p in enumerate(cycle(pl)):
                if i >= 6000: break
                if not p.dead:
                    g.process_action(PlayerTurn(p))
        except GameEnded:
            pass

    def can_leave(self, p):
        return getattr(p, 'dead', False)

class THBattleIdentity5(THBattleIdentity):
    n_persons = 5
    T = Identity.TYPE

    identities = [
        T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T
