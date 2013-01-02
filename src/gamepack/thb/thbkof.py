# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList
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


class NextCharacter(Exception):
    def __init__(self, player):
        Exception.__init__(self)
        self.player = player


class KOFTryRevive(TryRevive):
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


class KOFPlayerDeath(PlayerDeath):
    def apply_action(self):
        tgt = self.target
        tgt.dead = True
        g = Game.getgame()
        src = self.source or self.target
        others = g.players.exclude(tgt)
        from .cards import VirtualCard
        from .actions import DropCards
        for cl in [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell, tgt.special]:
            if not cl: continue
            others.reveal(list(cl))
            g.process_action(DropCards(tgt, cl))
            assert not cl
        return True


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        g = Game.getgame()
        if evt_type == 'action_after' and isinstance(act, BaseDamage):
            tgt = act.target
            if tgt.life > 0: return act
            if not g.process_action(TryRevive(tgt, dmgact=act)):
                g.process_action(PlayerDeath(act.source, tgt))

                if not tgt.characters:
                    pl = g.players[:]
                    pl.remove(tgt)
                    g.winners = pl
                    raise GameEnded
                else:
                    g.next_character(tgt)
                    g.update_event_handlers()
                    g.process_action(DrawCards(tgt, 4))
                    tgt.dead = False
                    g.emit_event('kof_next_character', tgt)
                    raise NextCharacter(tgt)

            pl = g.players
            if pl[0].dropped:
                g.winners = [pl[1]]
                raise GameEnded

            if pl[1].dropped:
                g.winners = [pl[0]]
                raise GameEnded

        return act


class KOFActionStage(ActionStage):
    def apply_action(self):
        while True:
            try:
                rst = ActionStage.apply_action(self)
            except NextCharacter as e:
                if e.player is not self.target:
                    continue
                raise
            break
        
        return rst


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
        
        self.action_types[ActionStage] = KOFActionStage
        self.action_types[PlayerDeath] = KOFPlayerDeath
        self.action_types[TryRevive] = KOFTryRevive

        from cards import Card, Deck, CardList

        self.deck = Deck()

        self.ehclasses = []

        for i, p in enumerate(self.players):
            p.cards = CardList(p, 'handcard') # Cards in hand
            p.showncards = CardList(p, 'showncard') # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips') # Equipments
            p.fatetell = CardList(p, 'fatetell') # Cards in the Fatetell Zone
            p.special = CardList(p, 'special') # used on special purpose

            p.showncardlists = [p.showncards, p.fatetell]

            p.tags = defaultdict(int)

            p.dead = False
            p.need_shuffle = False
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i%2]

        # choose girls -->
        from characters import characters as chars
        from characters.akari import Akari

        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(random.sample(chars, 10), xrange(10))
            ]

            for c in random.sample(choice, 4):
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
        random.shuffle(roll)
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
            random.shuffle(perm)
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
                if not p.dead:
                    self.emit_event('player_turn', p)
                    try:
                        self.process_action(PlayerTurn(p))
                    except NextCharacter:
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
        p.skills = cls.skills[:] # make it instance variable
        p.maxlife = cls.maxlife
        p.life = cls.maxlife
        tags = p.tags

        for k in tags.keys():
            del tags[k]
            
        ehs = self.ehclasses
        if old:
            for s in old.skills:
                try:
                    ehs.remove(s)
                except ValueError:
                    pass

        ehs.extend(p.eventhandlers_required)

