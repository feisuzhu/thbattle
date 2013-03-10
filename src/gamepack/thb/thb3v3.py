# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList, InterruptActionFlow
from game import TimeLimitExceeded

from actions import *
from itertools import cycle
from collections import defaultdict
import random

from utils import BatchList, check, CheckFailed, classmix, Enum

from .common import *

import logging
log = logging.getLogger('THBattle')

_game_ehs = {}
def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls

_game_actions = {}
def game_action(cls):
    _game_actions[cls.__name__] = cls
    return cls

class ActFirst(object): # for choose_option
    pass

class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2

class THBattle(GameBase):
    n_persons = 6
    game_ehs = _game_ehs
    game_actions = _game_actions
    order_list = (0, 5, 3, 4, 2, 1)
    
    def on_player_dead(g, tgt, src):
        force1, force2 = g.forces
        if all(p.dead or p.dropped for p in force1):
            g.winners = force2[:]
            raise GameEnded

        if all(p.dead or p.dropped for p in force2):
            g.winners = force1[:]
            raise GameEnded

    def init_identities(self, sample):
        T = Identity.TYPE
        self.forces = forces = BatchList([PlayerList(), PlayerList()])
        pl = self.players

        for i, p in enumerate(pl):
            p.identity = Identity()
            f = i % 2
            p.identity.type = (T.HAKUREI, T.MORIYA)[f]
            p.force = f
            forces[f].append(p)

        for p in pl:
            self.process_action(RevealIdentity(p, pl))

    def roll_and_choose_girls(self, sample):
        ehclasses = list(action_eventhandlers) + self.game_ehs.values()
        # choose girls -->
        from characters import characters as chars
        from characters.akari import Akari
        
        #roll
        roll = range(len(self.players))
        if not sample:
            random.shuffle(roll)
        pl = self.players
        roll = sync_primitive(roll, pl)
        roll = [pl[i] for i in roll]

        self.emit_event('game_roll', roll)
        first = roll[0]
        self.emit_event('game_roll_result', first)

        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(random.sample(chars, 16), xrange(16))
            ]
            
            if sample:
                for i, c in enumerate(sample):
                    choice[i] = CharChoice(c, i)
            else:
                for c in random.sample(choice, 4):
                    c.real_cls = c.char_cls
                    c.char_cls = Akari

        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(16)
            ]

        self.players.reveal(choice)
        first_index = self.players.index(first)
        n = len(self.order_list)
        order = [self.players[(first_index + i) % n] for i in self.order_list]

        def mix(p, c):
            # mix char class with player -->
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:] # make it instance variable
            p.life = p.maxlife
            ehclasses.extend(p.eventhandlers_required)

        # akaris = {}  # DO NOT USE DICT! THEY ARE UNORDERED!
        akaris = []
        self.emit_event('choose_girl_begin', (self.players, choice))
        for i, p in enumerate(order):
            cid = p.user_input('choose_girl', choice, timeout=(n-i+1)*5)
            try:
                check(isinstance(cid, int))
                check(0 <= cid < len(choice))
                c = choice[cid]
                check(not c.chosen)
                c.chosen = p
            except CheckFailed:
                # first non-chosen char 
                for c in choice:
                    if not c.chosen:
                        c.chosen = p
                        break

            if issubclass(c.char_cls, Akari):
                akaris.append((p, c))
            else:
                mix(p, c)

            self.emit_event('girl_chosen', c)

        self.emit_event('choose_girl_end', None)

        # reveal akaris
        if akaris:
            for p, c in akaris:
                c.char_cls = c.real_cls

            self.players.reveal([i[1] for i in akaris])

            for p, c in akaris:
                mix(p, c)

        self.event_handlers = EventHandler.make_list(ehclasses)
        return first

    def init_game(self, first_actor):
        self.emit_event('game_begin', self)

        for p in self.players:
            self.process_action(
                DrawCards(p, amount=3 if p is first_actor else 4)
            )

    def can_leave(self, p):
        return getattr(p, 'dead', False)
