# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, get_seed_for
from game.autoenv import user_input
from thb.actions import DistributeCards, GenericAction, MigrateCardsTransaction, PlayerDeath
from thb.actions import PlayerTurn, RevealIdentity, action_eventhandlers, migrate_cards
from thb.characters.baseclasses import mixin_character
from thb.common import PlayerIdentity, build_choices, roll
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet, SortCharacterInputlet
from utils import BatchList, Enum


# -- code --
log = logging.getLogger('THBattle')

_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    interested = ('action_after', 'action_apply')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()

            tgt = act.target
            force = tgt.force
            if len(force.pool) <= 1:
                forces = g.forces[:]
                forces.remove(force)
                g.winners = forces[0][:]
                g.game_end()

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            g = Game.getgame()

            tgt = act.target
            pool = tgt.force.pool
            assert pool

            mapping = {tgt: pool}
            with InputTransaction('ChooseGirl', [tgt], mapping=mapping) as trans:
                c = user_input([tgt], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                c = c or [_c for _c in pool if not _c.chosen][0]
                c.chosen = tgt
                pool.remove(c)
                trans.notify('girl_chosen', (tgt, c))

            tgt = g.switch_character(tgt, c)

            c = getattr(g, 'current_player', None)

            g.process_action(DistributeCards(tgt, 4))

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(RedrawCards(tgt, tgt))

        return act


class RedrawCards(DistributeCards):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()

        with MigrateCardsTransaction(self) as trans:
            g.players.reveal(list(tgt.cards))
            migrate_cards(tgt.cards, g.deck.droppedcards, trans=trans)
            cards = g.deck.getcards(4)
            tgt.reveal(cards)
            migrate_cards(cards, tgt.cards, trans=trans)

        return True


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattleFaithBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = Game.getgame()
        params = self.params

        from thb.cards import Deck

        g.picks = []
        g.deck = Deck(ppoints=(1, 1, 1, 1, 1, 2))

        g.ehclasses = list(action_eventhandlers) + g.game_ehs.values()

        H, M = Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA
        if params['random_seat']:
            # reseat
            seed = get_seed_for(g.players)
            random.Random(seed).shuffle(g.players)
            g.emit_event('reseat', None)

            L = [[H, H, M, M, H, M], [H, M, H, M, H, M]]
            rnd = random.Random(get_seed_for(g.players))
            L = rnd.choice(L) * 2
            s = rnd.randrange(0, 6)
            idlist = L[s:s+6]
            del L, s, rnd
        else:
            idlist = [H, M, H, M, H, M]

        del H, M

        for p, identity in zip(g.players, idlist):
            p.identity = Identity()
            p.identity.type = identity
            g.process_action(RevealIdentity(p, g.players))

        force_hakurei      = BatchList()
        force_moriya       = BatchList()
        force_hakurei.pool = []
        force_moriya.pool  = []

        for p in g.players:
            if p.identity.type == Identity.TYPE.HAKUREI:
                force_hakurei.append(p)
                p.force = force_hakurei
            elif p.identity.type == Identity.TYPE.MORIYA:
                force_moriya.append(p)
                p.force = force_moriya

        g.forces = BatchList([force_hakurei, force_moriya])

        roll_rst = roll(g, self.items)
        first = roll_rst[0]

        # choose girls -->
        from . import characters
        chars = characters.get_characters('faith')

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=g.players,
            num=[4] * 6, akaris=[1] * 6,
            shared=False,
        )

        rst = user_input(g.players, SortCharacterInputlet(g, choices, 2), timeout=30, type='all')

        for p in g.players:
            a, b = [choices[p][i] for i in rst[p][:2]]
            b.chosen = None
            p.force.reveal(b)
            g.switch_character(p, a)
            p.force.pool.append(b)

        for p in g.players:
            if p.player is first:
                first = p
                break

        pl = g.players
        first_index = pl.index(first)
        order = BatchList(range(len(pl))).rotate_to(first_index)

        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        g.emit_event('game_begin', g)

        for p in pl:
            g.process_action(DistributeCards(p, amount=4))

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

        return True


class THBattleFaith(Game):
    n_persons    = 6
    game_ehs     = _game_ehs
    bootstrap    = THBattleFaithBootstrap
    params_def   = {
        'random_seat': (True, False),
    }

    def can_leave(g, p):
        return False

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.set_event_handlers(EventHandler.make_list(ehclasses))

    def switch_character(g, p, choice):
        choice.akari = False

        g.players.reveal(choice)
        cls = choice.char_cls

        g.picks.append(cls)
        log.info(u'>> NewCharacter: %s %s', Identity.TYPE.rlookup(p.identity.type), cls.__name__)

        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)
        g.forces[0].replace(old, p)
        g.forces[1].replace(old, p)

        ehs = g.ehclasses
        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()
        g.emit_event('switch_character', (old, p))

        return p

    def decorate(g, p):
        from thb.cards import CardList
        p.cards          = CardList(p, 'cards')       # Cards in hand
        p.showncards     = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')      # Equipments
        p.fatetell       = CardList(p, 'fatetell')    # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')     # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags           = defaultdict(int)

    def get_remaining_characters(g):
        try:
            hakurei, moriya = g.forces
        except:
            return -1, -1

        h, m = len(hakurei.pool) - 1, len(moriya.pool) - 1
        if h < 0 or m < 0:
            return -1, -1

        return h, m

    def get_stats(g):
        return [{'event': 'pick', 'attributes': {
            'character': p.__name__,
            'gamemode': g.__class__.__name__,
            'identity': '-',
            'victory': None,
        }} for p in g.picks]
