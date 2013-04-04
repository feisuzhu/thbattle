# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList, InterruptActionFlow
from game import TimeLimitExceeded

from actions import *
from itertools import cycle
from collections import defaultdict

from utils import BatchList, check, CheckFailed, classmix, Enum

from .common import *

import logging
log = logging.getLogger('THBattle')

_game_ehs = {}
def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target
        
        g = Game.getgame()

        if not tgt.characters:
            pl = g.players[:]
            pl.remove(tgt)
            g.winners = pl
            raise GameEnded

        pl = g.players
        if pl[0].dropped:
            g.winners = [pl[1]]
            raise GameEnded

        if pl[1].dropped:
            g.winners = [pl[0]]
            raise GameEnded

        return act


@game_eh
class KOFCharacterSwitchHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_stage_action' or \
            (evt_type in { 'action_before', 'action_after' } and isinstance(act, PlayerTurn)):
                self.do_switch()

        return act

    @staticmethod
    def do_switch():
        g = Game.getgame()

        for p in [p for p in g.players if p.dead and p.characters]:
            g.next_character(p)
            g.update_event_handlers()
            p.dead = False
            g.process_action(DrawCards(p, 4))
            g.emit_event('kof_next_character', p)


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleKOF(Game):
    n_persons = 2
    game_ehs = _game_ehs

    def game_start(self):
        # game started, init state
        
        from cards import Card, Deck, CardList

        self.deck = Deck()

        self.ehclasses = []

        for i, p in enumerate(self.players):
            init_basic_card_lists(p)
            p.tags = defaultdict(int)
            p.dead = False
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i%2]

        # choose girls -->
        from characters import characters as chars
        from characters.akari import Akari

        _chars = self.random.sample(chars, 10)
        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(_chars[-10:], xrange(10))
            ]

            for c in self.random.sample(choice, 4):
                c.real_cls = c.char_cls
                c.char_cls = Akari

        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(10)
            ]

        # -----------

        self.players.reveal(choice)

        # roll
        roll = range(len(self.players))
        self.random.shuffle(roll)
        pl = self.players
        roll = sync_primitive(roll, pl)

        roll = [pl[i] for i in roll]

        self.emit_event('game_roll', roll)

        first = roll[0]
        second = roll[1]

        self.emit_event('game_roll_result', first)
        # ----

        # akaris = {}  # DO NOT USE DICT! THEY ARE UNORDERED!
        akaris = []
        self.emit_event('choose_girl_begin', (self.players, choice))

        A, B = first, second
        order = [A, B, B, A, A, B, B, A, A, B]
        A.choices = []
        B.choices = []
        del A, B

        for i, p in enumerate(order):
            cid = p.user_input('choose_girl', choice, timeout=10)
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

            p.choices.append(c)

            self.emit_event('girl_chosen', c)

        self.emit_event('choose_girl_end', None)

        # reveal akaris for themselves
        for p, c in akaris:
            c.char_cls = c.real_cls
            p.reveal(c)

        for p in self.players:
            perm = range(5)
            self.random.shuffle(perm)
            perm = sync_primitive(perm, p)
            p._perm = perm

        def process(p, input):
            try:
                check(input)
                check_type([int, Ellipsis], input)
                check(len(set(input)) == len(input))
                check(all(0 <= i < 5 for i in input))
                p._perm_input = input
            except CheckFailed:
                p._perm_input = range(5)

        self.players.user_input_all('kof_sort_characters', process, None, 30)

        # reveal akaris for both
        if akaris:
            for p, c in akaris:
                c.char_cls = c.real_cls

            self.players.reveal([i[1] for i in akaris])

        # reveal _perm
        first._perm = sync_primitive(first._perm, self.players)
        second._perm = sync_primitive(second._perm, self.players)

        for p in self.players:
            perm = p.choices
            perm = [perm[i] for i in p._perm]
            perm = [perm[i] for i in p._perm_input[:3]]
            p.characters = [c.char_cls for c in perm]
            del p.choices

        self.next_character(first)
        self.next_character(second)

        self.update_event_handlers()

        try:
            pl = self.players
            for p in pl:
                self.process_action(RevealIdentity(p, pl))

            self.emit_event('game_begin', self)

            for p in pl:
                self.process_action(DrawCards(p, amount=3 if p is second else 4))

            for i, p in enumerate(cycle([second, first])):
                if i >= 6000: break
                if p.dead:
                    assert p.characters  # if not holds true, DeathHandler should end game.
                    KOFCharacterSwitchHandler.do_switch()

                assert not p.dead

                try:
                    self.emit_event('player_turn', p)
                    self.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        except GameEnded:
            pass

    def can_leave(self, p):
        return False

    def update_event_handlers(self):
        ehclasses = list(action_eventhandlers) + self.game_ehs.values()
        ehclasses += self.ehclasses
        self.event_handlers = EventHandler.make_list(ehclasses)

    def next_character(self, p):
        assert p.characters
        cls = p.characters.pop(0)

        # mix char class with player -->
        old = mixin_character(p, cls)
        p.skills = list(cls.skills)  # make it instance variable
        p.maxlife = cls.maxlife
        p.life = cls.maxlife
        tags = p.tags

        for k in list(tags):
            del tags[k]
            
        ehs = self.ehclasses
        if old:
            for eh in old.eventhandlers_required:
                try:
                    ehs.remove(eh)
                except ValueError:
                    pass

        ehs.extend(p.eventhandlers_required)

