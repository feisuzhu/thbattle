# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList, InterruptActionFlow

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

class Identity(PlayerIdentity):
    # 城管 BOSS 道中 黑幕
    class TYPE:
        HIDDEN = 0
        ATTACKER = 1
        BOSS = 2
        ACCOMPLICE = 3
        CURTAIN = 4


class THBattleIdentity(GameBase):
    n_persons = 8
    game_actions = _game_actions
    T = Identity.TYPE
    identities = [
        T.ATTACKER, T.ATTACKER, T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE, T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T

    def on_player_dead(g, tgt, src):
        if src:
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

    def init_identities(g, sample):
        if not sample:
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
        if sample:
            for i, id in enumerate(sample):
                il[i] = id
            idx = 1
        else:
            idx = random.randrange(len(g.players))
            
        pl = g.players
        idx = sync_primitive(idx, g.players)
        # pl[-1], pl[idx] = pl[idx], pl[-1]
        boss = g.boss = pl[idx]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS
        g.process_action(RevealIdentity(boss, g.players))

        for p in g.players.exclude(boss):
            p.identity = Identity()
            id = il.pop()
            if Game.SERVER_SIDE:
                p.identity.type = id
            g.process_action(RevealIdentity(p, p))

    def roll_and_choose_girls(g, sample):
        ehclasses = list(action_eventhandlers) + _game_ehs.values()
        boss = g.boss
        # choose girls init -->
        from characters import characters as chars

        chars = chars[:]
        random.shuffle(chars)

        choices = None
        chosen_girls = []

        def getchoice(pid, n):
            return [CharChoice(
                        None if Game.CLIENT_SIDE
                        else sample[pid] if sample
                        else chars.pop(),
                        cid
                    ) for cid in xrange(n)]

        def putback():
            chars.extend(
                c.char_cls for cl in choices
                for c in cl if not c.chosen
            )
            random.shuffle(chars)

        pl = PlayerList(g.players)
        def process(p, cid):
            try:
                check(isinstance(cid, int))
                i, n = p._choose_tag
                check(0 <= cid < n)

                c = choices[i][cid]
                c.chosen = p
                chosen_girls.append(c)
                g.emit_event('girl_chosen', c)
                pl.remove(p)
                return c

            except CheckFailed as e:
                return None

            finally:
                try:
                    del p._choose_tag
                except AttributeError:
                    pass

        #for i, p in enumerate(pl):
        #    p._choose_tag = i
        #    p.reveal(choice[i*3:(i+1)*3])
        #
        #boss.reveal(choice[-2:])
        
        choices = [getchoice(0, 5)]
        boss.reveal(choices[0])
        boss._choose_tag = (0, 5)
        
        g.emit_event('choose_girl_begin', ([boss], choices[0]))
        PlayerList([boss]).user_input_all(
            'choose_girl', process, choices[0], timeout=30
        )

        if Game.SERVER_SIDE: putback()
        
        if not chosen_girls:
            # didn't choose
            c = getchoice(0, 1)[0]
            c.chosen = boss
            chosen_girls.append(c)
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

        boss.life = boss.maxlife

        g.emit_event('choose_girl_end', None)


        choices = []
        
        for i, p in enumerate(pl):
            p._choose_tag = (i, 3)
            choices.append(getchoice(i + 1, 3))
            p.reveal(choices[i])
            g.emit_event('choose_girl_begin', ([p], choices[i]))

        choices_flat = [c for cl in choices for c in cl]

        pl.user_input_all('choose_girl', process, choices_flat, timeout=30)
        g.emit_event('choose_girl_end', None)
        
        if Game.SERVER_SIDE: putback()
        
        # if there's any person didn't make a choice -->
        for p in pl:
            c = getchoice(0, 1)[0]
            c.chosen = p
            chosen_girls.append(c)
            g.emit_event('girl_chosen', c)

        # now you can have them all.
        g.players.reveal(chosen_girls)

        # mix char class with player -->
        for c in chosen_girls:
            p = c.chosen
            if p is boss: continue # already mixed
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:] # make it instance variable
            p.life = p.maxlife
            ehclasses.extend(p.eventhandlers_required)
        
        g.event_handlers = EventHandler.make_list(ehclasses)

        return boss

    def init_game(g, f):
        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DrawCards(p, amount=4))

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

