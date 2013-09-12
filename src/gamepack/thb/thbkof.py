# -*- coding: utf-8 -*-
import random
from itertools import cycle
from collections import defaultdict
import logging

from utils import Enum

from game.autoenv import Game, EventHandler, GameEnded, InterruptActionFlow, InputTransaction, user_input
from game import sync_primitive

from .common import PlayerIdentity, CharChoice, mixin_character, get_seed_for

from .actions import PlayerDeath, UserAction, PlayerTurn, DrawCards, RevealIdentity
from .actions import action_eventhandlers

from .inputlets import ChooseGirlInputlet, KOFSortInputlet

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

        if tgt is g.current_turn:
            for a in reversed(g.action_stack):
                isinstance(a, UserAction) and a.interrupt_after_me()

        return act


@game_eh
class KOFCharacterSwitchHandler(EventHandler):
    def handle(self, evt_type, act):
        cond = evt_type in ('action_before', 'action_after')
        cond = cond and isinstance(act, PlayerTurn)
        cond = cond or evt_type == 'action_stage_action'
        cond and self.do_switch()
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

    def game_start(g):
        # game started, init state

        from cards import Deck, CardList

        g.deck = Deck()

        g.ehclasses = []

        for i, p in enumerate(g.players):
            p.cards = CardList(p, 'cards')  # Cards in hand
            p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips')  # Equipments
            p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
            p.special = CardList(p, 'special')  # used on special purpose

            p.showncardlists = [p.showncards, p.fatetell]

            p.tags = defaultdict(int)

            p.dead = False
            p.identity = Identity()
            p.identity.type = (Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA)[i % 2]

        # choose girls -->
        from characters import characters as chars
        from characters.akari import Akari
        from characters.mokou1 import Mokou as Mokou1
        from characters.mokou2 import Mokou as Mokou2

        _chars = g.random.sample(chars, 10)
        _chars.append(Mokou1)
        _chars.append(Mokou2)
        if Game.SERVER_SIDE:
            choice = [CharChoice(cls) for cls in _chars[-10:]]

            for c in g.random.sample(choice, 4):
                c.real_cls = c.char_cls
                c.char_cls = Akari

        elif Game.CLIENT_SIDE:
            choice = [CharChoice(None) for i in xrange(10)]

        # -----------

        g.players.reveal(choice)

        # roll
        roll = range(len(g.players))
        g.random.shuffle(roll)
        pl = g.players
        roll = sync_primitive(roll, pl)

        roll = [pl[i] for i in roll]

        g.emit_event('game_roll', roll)

        first = roll[0]
        second = roll[1]

        g.emit_event('game_roll_result', first)
        # ----

        # akaris = {}  # DO NOT USE DICT! THEY ARE UNORDERED!
        akaris = []

        A, B = first, second
        order = [A, B, B, A, A, B, B, A, A, B]
        A.choices = []
        B.choices = []
        choice_mapping = {A: choice, B: choice}
        del A, B

        with InputTransaction('ChooseGirl', g.players, mapping=choice_mapping) as trans:
            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, choice_mapping), 10, 'single', trans)
                if not c:
                    # first non-chosen char
                    for c in choice:
                        if not c.chosen:
                            c.chosen = p
                            break

                if issubclass(c.char_cls, Akari):
                    akaris.append((p, c))

                c.chosen = p
                p.choices.append(c)

                trans.notify('girl_chosen', c)

        # reveal akaris for themselves
        for p, c in akaris:
            c.char_cls = c.real_cls
            p.reveal(c)

        for p in g.players:
            seed = get_seed_for(p)
            random.Random(seed).shuffle(p.choices)

        mapping = {first: first.choices, second: second.choices}
        rst = user_input(g.players, KOFSortInputlet(g, mapping), timeout=30, type='all')

        for p in g.players:
            perm = p.choices
            perm = [perm[i] for i in rst[p][:3]]
            p.characters = [c.char_cls for c in perm]
            del p.choices

        g.next_character(first)
        g.next_character(second)

        g.update_event_handlers()

        try:
            pl = g.players
            for p in pl:
                g.process_action(RevealIdentity(p, pl))

            g.emit_event('game_begin', g)

            for p in pl:
                g.process_action(DrawCards(p, amount=3 if p is second else 4))

            for i, p in enumerate(cycle([second, first])):
                if i >= 6000: break
                if p.dead:
                    assert p.characters  # if not holds true, DeathHandler should end game.
                    KOFCharacterSwitchHandler.do_switch()

                assert not p.dead

                try:
                    g.emit_event('player_turn', p)
                    g.process_action(PlayerTurn(p))
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
        char = CharChoice(p.characters.pop(0))
        self.players.reveal(char)
        cls = char.char_cls

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
