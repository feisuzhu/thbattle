# -*- coding: utf-8 -*-
import random
import time

from game.autoenv import Game, EventHandler, GameEnded, InterruptActionFlow, user_input, InputTransaction

from .actions import PlayerDeath, DrawCards, PlayerTurn, RevealIdentity, UserAction
from .actions import action_eventhandlers, migrate_cards

from .characters.baseclasses import mixin_character

from itertools import cycle
from collections import defaultdict

from utils import BatchList, Enum

from .common import PlayerIdentity, get_seed_for, sync_primitive, CharChoice
from .inputlets import ChooseGirlInputlet, ChooseOptionInputlet, SortCharacterInputlet

import logging
log = logging.getLogger('THBattle')

_game_ehs = {}
_game_actions = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, PlayerDeath): return act

        g = Game.getgame()

        tgt = act.target
        force = tgt.force
        if len(force.pool) <= 1:
            forces = g.forces[:]
            forces.remove(force)
            g.winners = forces[0][:]
            raise GameEnded

        g = Game.getgame()

        pool = tgt.force.pool
        assert pool

        mapping = {tgt: pool}
        with InputTransaction('ChooseGirl', [tgt], mapping=mapping) as trans:
            c = user_input([tgt], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
            c = c or [_c for _c in pool if not _c.chosen][0]
            c.chosen = tgt
            pool.remove(c)
            trans.notify('girl_chosen', c)

        tgt = g.switch_character(tgt, c)
        g.process_action(DrawCards(tgt, 4))

        if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            g.process_action(RedrawCards(tgt, tgt))

        return act


class RedrawCards(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()

        # Fire events after job done.
        # Looks like atomic.

        oldcards = list(tgt.cards)
        migrate_cards(tgt.cards, g.deck.droppedcards, no_event=True)
        cards = g.deck.getcards(4)
        tgt.reveal(cards)
        migrate_cards(cards, tgt.cards, no_event=True)

        g.emit_event('card_migration', (self, oldcards, tgt.cards, g.deck.droppedcards))
        g.emit_event('card_migration', (self, cards, g.deck.cards, tgt.cards))

        return True


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleFaith(Game):
    n_persons = 6
    game_ehs = _game_ehs
    game_actions = _game_actions

    def game_start(g):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = list(action_eventhandlers) + g.game_ehs.values()

        # reseat
        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(g.players)
        g.emit_event('reseat', None)

        H, M = Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA
        L = [[H, H, M, M, H, M], [H, M, H, M, H, M]]
        rnd = random.Random(get_seed_for(g.players))
        L = rnd.choice(L) * 2
        s = rnd.randrange(0, 6)
        idlist = L[s:s+6]
        del H, M, L, s, rnd

        for p, identity in zip(g.players, idlist):
            p.identity = Identity()
            p.identity.type = identity
            g.process_action(RevealIdentity(p, g.players))

        force_hakurei = BatchList()
        force_moriya = BatchList()
        force_hakurei.pool = []
        force_moriya.pool = []

        for p in g.players:
            if p.identity.type == Identity.TYPE.HAKUREI:
                force_hakurei.append(p)
                p.force = force_hakurei
            elif p.identity.type == Identity.TYPE.MORIYA:
                force_moriya.append(p)
                p.force = force_moriya

        g.forces = BatchList([force_hakurei, force_moriya])

        # ----- roll ------
        roll = range(len(g.players))
        g.random.shuffle(roll)
        pl = g.players
        roll = sync_primitive(roll, pl)
        roll = [pl[i] for i in roll]
        g.emit_event('game_roll', roll)
        first = roll[0]
        g.emit_event('game_roll_result', first)
        # ----

        # choose girls -->
        from . import characters
        chars = list(characters.characters)
        g.random.shuffle(chars)

        if Game.SERVER_SIDE:
            choices = [CharChoice(cls) for cls in chars[-24:]]
        else:
            choices = [CharChoice(None) for _ in xrange(24)]

        del chars[-24:]

        for p in g.players:
            c = choices[-3:]
            del choices[-3:]
            akari = CharChoice(characters.akari.Akari)
            akari.real_cls = chars.pop()
            c.append(akari)
            p.choices = c
            p.choices_chosen = []
            p.reveal(c)

        mapping = {p: p.choices for p in g.players}

        rst = user_input(g.players, SortCharacterInputlet(g, mapping, 2), timeout=30, type='all')
        for p in g.players:
            p.choices_chosen = [mapping[p][i] for i in rst[p][:2]]
        
        for p in g.players:
            a, b = p.choices_chosen
            b.chosen = None
            p.force.reveal(b)
            g.switch_character(p, a)
            p.force.pool.append(b)
            del p.choices_chosen

        for p in g.players:
            if p.player is first:
                first = p
                break

        try:
            pl = g.players
            first_index = pl.index(first)
            order = BatchList(range(len(pl))).rotate_to(first_index)

            for p in pl:
                g.process_action(RevealIdentity(p, pl))

            g.emit_event('game_begin', g)

            for p in pl:
                g.process_action(DrawCards(p, amount=4))

            pl = g.players.rotate_to(first)
            rst = user_input(pl[1:], ChooseOptionInputlet(DeathHandler(), (False, True)), type='all')

            for p in pl[1:]:
                rst.get(p) and g.process_action(RedrawCards(p, p))

            pl = g.players
            for i, idx in enumerate(cycle(order)):
                if i >= 6000: break
                p = pl[idx]
                if p.dead: continue

                g.emit_event('player_turn', p)
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        except GameEnded:
            pass

        log.info(u'>> Winner: %s', Identity.TYPE.rlookup(g.winners[0].identity.type))

    def can_leave(g, p):
        return False

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.event_handlers = EventHandler.make_list(ehclasses)

    def switch_character(g, p, choice):
        choice.char_cls = choice.real_cls or choice.char_cls  # reveal akari

        g.players.reveal(choice)
        cls = choice.char_cls

        log.info(u'>> NewCharacter: %s %s', Identity.TYPE.rlookup(p.identity.type), cls.__name__)

        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)
        g.forces[0].replace(old, p)
        g.forces[1].replace(old, p)

        ehs = g.ehclasses
        if oldcls:
            for eh in oldcls.eventhandlers_required:
                try:
                    ehs.remove(eh)
                except ValueError:
                    pass

        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()
        g.emit_event('switch_character', p)

        return p

    def decorate(g, p):
        from cards import CardList
        p.cards = CardList(p, 'cards')  # Cards in hand
        p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips = CardList(p, 'equips')  # Equipments
        p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
        p.special = CardList(p, 'special')  # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags = defaultdict(int)
