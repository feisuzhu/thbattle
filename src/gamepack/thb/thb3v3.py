# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList
from game import TimeLimitExceeded

from actions import *
from itertools import cycle
from collections import defaultdict
import random

from utils import BatchList, check, CheckFailed, classmix

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

@game_action
class TryRevive(TryRevive):
    def __init__(self, target, dmgact):
        self.source = self.target = target
        self.dmgact = dmgact
        g = Game.getgame()
        if target.dead:
            log.error('TryRevive buggy condition, __init__')
            return
        self.asklist = BatchList(
            p for p in g.players if not p.dead
        ).rotate_to(target)

    def apply_action(self):
        tgt = self.target
        if tgt.tags['in_tryrevive']:
            # nested TryRevive, just return True
            # will trigger when Eirin uses Diamond Exinwan to heal self
            return True

        if tgt.dead:
            log.error('TryRevive buggy condition, apply')
            import traceback
            traceback.print_stack()
            return False

        tgt.tags['in_tryrevive'] = True
        g = Game.getgame()
        pl = self.asklist
        from .cards import UseHeal
        for p in pl:
            while True:
                act = UseHeal(p)
                if g.process_action(act):
                    cards = act.cards
                    if not cards: continue
                    from .cards import Heal
                    g.process_action(Heal(p, tgt))
                    if tgt.life > 0:
                        tgt.tags['in_tryrevive'] = False
                        return True
                    continue
                break
        tgt.tags['in_tryrevive'] = False
        return tgt.life > 0

@game_action
class PlayerDeath(PlayerDeath):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.dead = True
        #dropped = g.deck.droppedcards
        src = self.source or self.target
        others = g.players.exclude(tgt)
        from .cards import VirtualCard
        from .actions import DropCards
        for cl in [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell, tgt.special]:
            if not cl: continue
            #l = [c for c in cl if not c.is_card(VirtualCard)]
            others.reveal(list(cl))
            g.process_action(DropCards(tgt, cl))
            #migrate_cards(l, dropped, unwrap=True)
            assert not cl
            #cl.clear()
        return True

@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        g = Game.getgame()
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.life > 0: return act
            if not g.process_action(TryRevive(tgt, dmgact=act)):
                g.process_action(PlayerDeath(act.source, tgt))

            # see if game ended
            force1, force2 = g.forces
            if all(p.dead or p.dropped for p in force1):
                g.winners = force2[:]
                raise GameEnded

            if all(p.dead or p.dropped for p in force2):
                g.winners = force1[:]
                raise GameEnded

        return act

class ActFirst(object): # for choose_option
    pass

class Identity(PlayerIdentity):
    class TYPE:
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2

class THBattle(Game):
    n_persons = 6
    game_ehs = _game_ehs
    game_actions = _game_actions
    order_list = (5, 4, 2, 3, 1, 0)

    def game_start(self):
        # game started, init state
        from cards import Card, Deck, CardList

        self.deck = Deck()

        ehclasses = list(action_eventhandlers) + self.game_ehs.values()

        self.forces = forces = BatchList([PlayerList(), PlayerList()])
        for i, p in enumerate(self.players):
            f = i%2
            p.force = f
            forces[f].append(p)

        # roll
        roll = range(len(self.players))
        random.shuffle(roll)
        pl = self.players
        roll = sync_primitive(roll, pl)

        roll = [pl[i] for i in roll]

        self.emit_event('game_roll', roll)

        first = roll[0]

        for p in roll:
            if p.user_input('choose_option', ActFirst):
                first = p
                break

        self.emit_event('game_roll_result', first)
        # ----

        # choose girls -->
        from characters import characters as chars

        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(random.sample(chars, 20), xrange(20))
            ]

        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(20)
            ]

        # -----------

        self.players.reveal(choice)

        first_index = self.players.index(first)
        n = len(self.order_list)
        order = [self.players[(first_index + i) % n] for i in self.order_list]

        self.emit_event('choose_girl_begin', (pl, choice))
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

            # mix char class with player -->
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:] # make it instance variable
            ehclasses.extend(p.eventhandlers_required)

            self.emit_event('girl_chosen', c)

        self.emit_event('choose_girl_end', None)

        # this will make UIEventHook the last one
        # BUT WHY? FORGOT BUT THIS CAUSES PROBLEMS, REVERT
        # PROBLEM:
        # Reject prompt string should appear when the action fired,
        # actually appears after the whole reject process finished,
        # IN REVERSE ORDER.
        #self.event_handlers[:] = EventHandler.make_list(ehclasses) + self.event_handlers
        self.event_handlers.extend(EventHandler.make_list(ehclasses))

        for i, p in enumerate(self.players):
            p.cards = CardList(p, 'handcard') # Cards in hand
            p.showncards = CardList(p, 'showncard') # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips') # Equipments
            p.fatetell = CardList(p, 'fatetell') # Cards in the Fatetell Zone
            p.special = CardList(p, 'special') # used on special purpose

            p.showncardlists = [p.showncards, p.fatetell]

            p.tags = defaultdict(int)

            p.life = p.maxlife
            p.dead = False
            p.need_shuffle = False
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i%2]

        try:
            pl = self.players
            for p in pl:
                self.process_action(RevealIdentity(p, pl))

            self.emit_event('game_begin', self)

            for p in self.players:
                # variable 'first': see the roll process before
                # swapped with choose girl process
                self.process_action(DrawCards(p, amount=4))

            pl = self.players.rotate_to(first)

            for i, p in enumerate(cycle(pl)):
                if i >= 6000: break
                if not p.dead:
                    self.emit_event('player_turn', p)
                    self.process_action(PlayerTurn(p))
        except GameEnded:
            pass

    def can_leave(self, p):
        return getattr(p, 'dead', False)


class THBattle1v1DBG(THBattle):
    n_persons = 2
    order_list = (1, 0)
