# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from itertools import cycle
from typing import Any, Dict, List
import logging
import random

# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import BootstrapAction, GameEnded, GameItem, InputTransaction, InterruptActionFlow
from game.base import Player, get_seed_for
from thb.actions import DistributeCards, MigrateCardsTransaction, PlayerDeath, PlayerTurn
from thb.actions import RevealRole, migrate_cards
from thb.cards.base import Deck
from thb.characters.base import Character
from thb.common import CharChoice, PlayerRole, build_choices, roll
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet, SortCharacterInputlet
from thb.mode import THBEventHandler, THBattle
from utils.misc import BatchList


# -- code --
log = logging.getLogger('THBattle')


class DeathHandler(THBEventHandler):
    interested = ['action_after', 'action_apply']
    game: 'THBattleFaith'

    def handle(self, evt_type: str, act: PlayerDeath) -> PlayerDeath:
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = self.game

            tgt = act.target
            role = g.roles[tgt.player].get()
            pool = g.pool[role]
            if len(pool) <= 1:
                raise GameEnded(g.forces[g.get_opponent_role(role)])

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            g = self.game

            tgt = act.target
            role = g.roles[tgt.player].get()
            pool = g.pool[role]

            mapping = {tgt.player: pool}
            with InputTransaction('ChooseGirl', [tgt], mapping=mapping) as trans:
                c = user_input([tgt], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                c = c or next(_c for _c in pool if not _c.chosen)
                c.chosen = tgt
                pool.remove(c)
                trans.notify('girl_chosen', (tgt.player, c))

            tgt = g.switch_character(tgt.player, c)
            g.process_action(DistributeCards(tgt, 4))

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(RedrawCards(tgt, tgt))

        return act


class RedrawCards(DistributeCards):
    def apply_action(self):
        tgt = self.target
        g = self.game

        with MigrateCardsTransaction(self) as trans:
            g.players.reveal(list(tgt.cards))
            migrate_cards(tgt.cards, g.deck.droppedcards, trans=trans)
            cards = g.deck.getcards(4)
            tgt.reveal(cards)
            migrate_cards(cards, tgt.cards, trans=trans)

        return True


class THBFaithRole(Enum):
    HIDDEN  = 0
    HAKUREI = 1
    MORIYA  = 2


class THBattleFaithBootstrap(BootstrapAction):
    game: 'THBattleFaith'

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.source = self.target = None
        self.params = params
        self.items = items
        self.players = players

    def apply_action(self) -> bool:
        g = self.game
        params = self.params
        pl = self.players

        g.deck = Deck(g)
        g.roles = {}

        H, M = THBFaithRole.HAKUREI, THBFaithRole.MORIYA
        if params['random_seat']:
            # reseat
            orig_pl = BatchList(pl)
            seed = get_seed_for(g, pl)
            random.Random(seed).shuffle(pl)
            g.emit_event('reseat', (orig_pl, pl))

            L = [[H, H, M, M, H, M], [H, M, H, M, H, M]]
            rnd = random.Random(get_seed_for(g, pl))
            L = rnd.choice(L) * 2
            s = rnd.randrange(0, 6)
            rl = L[s:s+6]
            del L, s, rnd
        else:
            rl = [H, M, H, M, H, M]

        for p, role in zip(pl, rl):
            g.roles[p] = PlayerRole(THBFaithRole)
            g.roles[p].set(role)
            g.process_action(RevealRole(p, pl))

        g.forces[H] = BatchList()
        g.forces[M] = BatchList()
        g.pool[H] = BatchList()
        g.pool[M] = BatchList()

        for p in pl:
            g.forces[g.roles[p].get()].append(p)

        roll_rst = roll(g, pl, self.items)

        # choose girls -->
        from . import characters
        chars = characters.get_characters('common', 'faith')

        choices, _ = build_choices(
            g, pl, self.items, chars,
            spec={p: {'num': 4, 'akaris': 1} for p in pl}
        )

        rst = user_input(g.players, SortCharacterInputlet(g, choices, 2), timeout=30, type='all')

        g.players = BatchList()
        first: Character

        for p in pl:
            a, b = [choices[p][i] for i in rst[p][:2]]

            ch = g.switch_character(p, a)

            if p is roll_rst[0]:
                first = ch
                first_index = len(g.players)

            g.players.append(ch)

            b.chosen = None
            g.forces[g.roles[p].get()].reveal(b)
            g.pool[g.roles[p].get()].append(b)

        order = BatchList(range(len(pl))).rotate_to(first_index)
        g.emit_event('game_begin', g)

        for p in pl:
            g.process_action(DistributeCards(p, amount=4))

        reordered = g.players.rotate_to(first)
        rst = user_input(reordered[1:], ChooseOptionInputlet(DeathHandler(g), (False, True)), type='all')

        for p in reordered[1:]:
            rst.get(p) and g.process_action(RedrawCards(p, p))

        for i, idx in enumerate(cycle(order)):
            if i >= 6000: break
            ch = g.players[idx]
            if ch.dead: continue

            try:
                g.process_action(PlayerTurn(ch))
            except InterruptActionFlow:
                pass

        return True


class THBattleFaith(THBattle):
    n_persons  = 6
    game_ehs   = [DeathHandler]
    bootstrap  = THBattleFaithBootstrap
    params_def = {
        'random_seat': (True, False),
    }

    forces: Dict[THBFaithRole, BatchList[Player]]
    pool: Dict[THBFaithRole, List[CharChoice]]

    def can_leave(g: THBattleFaith, p: Any):
        return False

    def switch_character(g, p: Player, choice: CharChoice) -> Character:
        choice.akari = False

        g.players.player.reveal(choice)
        cls = choice.char_cls

        assert cls

        log.info('>> NewCharacter: %s %s', g.roles[p].get().name, cls.__name__)

        new = cls(p)
        g.players.find_replace(lambda ch: ch.player is p, new)
        g.refresh_dispatcher()

        g.emit_event('switch_character', (p, new))

        return new

    def get_opponent_role(g, r: THBFaithRole) -> THBFaithRole:
        if r == THBFaithRole.MORIYA:
            return THBFaithRole.HAKUREI
        elif r == THBFaithRole.MORIYA:
            return THBFaithRole.HAKUREI
        else:
            assert False, 'WTF!'
