# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from actions import DeadDropCards, DistributeCards, PlayerDeath, PlayerTurn, RevealIdentity
from actions import action_eventhandlers, migrate_cards
from characters.baseclasses import mixin_character
from common import CharChoice, PlayerIdentity, get_seed_for, sync_primitive
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, user_input
from inputlets import ChooseGirlInputlet
from utils import BatchList, Enum, filter_out

# -- code --
log = logging.getLogger('THBattleCP3')

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
        if evt_type == 'action_before' and isinstance(act, DeadDropCards):
            tgt = act.target
            g = Game.getgame()

            cp = [p for p in g.forces[tgt.force] if not p.dead]
            if not cp: return act

            assert len(cp) == 1
            cp = cp[0]
            cards = []
            for cl in (tgt.cards, tgt.showncards, tgt.equips):
                cards.extend(cl)

            cp.reveal(cards)
            migrate_cards(cards, cp.cards)

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            g = Game.getgame()

            # see if game ended
            alive = [p.force for p in g.players
                     if not (p.dead or p.dropped)]

            if len(set(alive)) == 1:
                g.winners = g.forces[alive[0]][:]
                g.game_end()

        return act


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        CP_A = 1
        CP_B = 2
        CP_C = 3


class THBattleCP3(Game):
    n_persons    = 6
    game_ehs     = _game_ehs
    game_actions = _game_actions
    params_def   = {}
    order_list   = (0, 5, 4, 3, 2, 1)

    def game_start(g, params):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        n_forces = g.n_persons / 2
        g.forces = forces = BatchList([
            BatchList() for i in xrange(n_forces)
        ])

        for i, p in enumerate(g.players):
            f = i % 3
            p.identity = Identity()
            p.identity.type = f + 1
            p.force = f
            forces[f].append(p)

        # choose girls -->
        from . import characters
        chars = characters.get_characters('3v3', 'cp3')

        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(chars)

        # ANCHOR(test)
        testing = []
        testing = filter_out(chars, lambda c: c.__name__ in testing)
        chars.extend(testing)

        choices = [CharChoice(cls) for cls in chars[-20:]]
        del chars[-16:]

        for c in choices[:4]:
            c.char_cls = characters.akari.Akari

        if Game.SERVER_SIDE:
            for c, cls in zip(choices[:4], g.random.sample(chars, 4)):  # yes, must random.sample
                c.real_cls = cls

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

        first_index = g.players.index(first)
        n = len(g.order_list)
        order = [g.players[(first_index + i) % n] for i in g.order_list]

        # akaris = {}  # DO NOT USE DICT! THEY ARE UNORDERED!
        akaris = []
        mapping = {p: choices for p in g.players}
        with InputTransaction('ChooseGirl', g.players, mapping=mapping) as trans:
            for p in order:
                c = user_input([p], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                c = c or [_c for _c in choices if not _c.chosen][0]
                c.chosen = p

                if issubclass(c.char_cls, characters.akari.Akari):
                    akaris.append((p, c))
                else:
                    g.set_character(p, c.char_cls)

                trans.notify('girl_chosen', (p, c))

        # reveal akaris
        if akaris:
            for p, c in akaris:
                c.char_cls = c.real_cls

            g.players.reveal([i[1] for i in akaris])

            for p, c in akaris:
                g.set_character(p, c.char_cls)

        g.event_handlers = EventHandler.make_list(ehclasses)

        # -------
        for p in g.players:
            log.info(
                u'>> Player: %s:%s %s',
                p.__class__.__name__,
                Identity.TYPE.rlookup(p.identity.type),
                p.account.username,
            )
        # -------

        first = g.players[first_index]

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=3 if p is first else 4))

        pl = g.players.rotate_to(first)

        for i, p in enumerate(cycle(pl)):
            if i >= 6000: break
            if not p.dead:
                g.emit_event('player_turn', p)
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def set_character(g, p, cls):
        # mix char class with player -->
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)
        for f in g.forces:
            f.replace(p, new)
        assert not old_cls
        ehs = g.ehclasses
        ehs.extend(cls.eventhandlers_required)
        g.emit_event('switch_character', new)
        return new

    def decorate(g, p):
        from .cards import CardList
        from .characters.baseclasses import Character
        assert isinstance(p, Character)

        p.cards = CardList(p, 'cards')  # Cards in hand
        p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips = CardList(p, 'equips')  # Equipments
        p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
        p.special = CardList(p, 'special')  # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags = defaultdict(int)
