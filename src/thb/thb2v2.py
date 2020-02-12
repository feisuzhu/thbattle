# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from itertools import cycle
from typing import Any, Dict, List, Set, Type
import logging
import random

# -- third party --
# -- own --
from game.base import BootstrapAction, Game, GameEnded, GameItem, InputTransaction
from game.base import InterruptActionFlow, Player, get_seed_for
from thb.actions import DeadDropCards, DistributeCards, DrawCardStage, DrawCards
from thb.actions import MigrateCardsTransaction, PlayerDeath, PlayerTurn, RevealRole, UserAction
from thb.actions import migrate_cards
from thb.cards.base import Deck
from thb.characters.base import Character
from thb.common import CharChoice, PlayerRole, roll
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet
from thb.mode import THBEventHandler, THBattle
from utils.misc import BatchList, partition
import settings


# -- code --
log = logging.getLogger('THBattle2v2')


class DeathHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act

        g = self.game
        tgt = act.target

        tgt = act.target
        dead = lambda p: p.dead or p.dropped or p is tgt

        # see if game ended
        force1, force2 = g.forces
        if all(dead(p) for p in force1):
            raise GameEnded(force2)

        if all(dead(p) for p in force2):
            raise GameEnded(force1)

        return act


class HeritageAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        lists = [tgt.cards, tgt.showncards, tgt.equips]
        with MigrateCardsTransaction(self) as trans:
            for cl in lists:
                if not cl: continue
                cl = list(cl)
                src.reveal(cl)
                migrate_cards(cl, src.cards, unwrap=True, trans=trans)

        return True


class HeritageHandler(THBEventHandler):
    interested = ['action_before']
    execute_after = ['DeathHandler', 'SadistHandler']

    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, DeadDropCards): return act

        g = self.game
        tgt = act.target
        for f in g.forces:
            if tgt in f:
                break
        else:
            assert False, 'WTF?!'

        other = BatchList(f).exclude(tgt)[0]
        if other.dead: return act

        if g.user_input([other], ChooseOptionInputlet(self, ('inherit', 'draw'))) == 'inherit':
            g.process_action(HeritageAction(other, tgt))

        else:
            g.process_action(DrawCards(other, 2))

        return act


class ExtraCardHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type != 'action_before':
            return act

        if not isinstance(act, DrawCardStage):
            return act

        g = self.game
        if g.draw_extra:
            act.amount += 1

        return act


class THB2v2Role(Enum):
    HIDDEN  = 0
    HAKUREI = 1
    MORIYA  = 2


class THBattle2v2Bootstrap(BootstrapAction):
    game: 'THBattle2v2'

    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.source = self.target = None
        self.params  = params
        self.items   = items
        self.players = players

    def apply_action(self) -> bool:
        g = self.game
        params = self.params
        items = self.items

        pl = self.players

        g.deck = Deck(g)
        g.roles = {}

        if params['random_force']:
            seed = get_seed_for(g, pl)
            random.Random(seed).shuffle(pl)

        g.draw_extra = params['draw_extra_card']

        H, M = THB2v2Role.HAKUREI, THB2v2Role.MORIYA
        g.forces = {H: BatchList(), M: BatchList()}

        for p, id in zip(pl, [H, H, M, M]):
            g.roles[p] = r = PlayerRole(THB2v2Role)
            g.roles[p].set(id)
            g.process_action(RevealRole(r, pl))

        roll_rst = roll(g, pl, items)
        '''
        winner = g.forces[roll_rst[0].identity.value]
        f1, f2 = partition(lambda ch: g.forces[ch.identity.value] is winner, roll_rst)
        final_order = [f1[0], f2[0], f2[1], f1[1]]
        '''
        g.emit_event('reseat', (pl, roll_rst))
        pl = roll_rst

        # ban / choose girls -->
        from . import characters
        chars = characters.get_characters('common', '2v2')

        seed = get_seed_for(g, pl)
        random.Random(seed).shuffle(chars)

        testing: List[str] = list(settings.TESTING_CHARACTERS)
        testing, chars = partition(lambda c: c.__name__ in testing, chars)
        chars.extend(testing)

        chars = chars[-20:]
        choices = [CharChoice(cls) for cls in chars]

        banned: Set[Type[Character]] = set()
        mapping = {p: choices for p in pl}
        with InputTransaction('BanGirl', pl, mapping=mapping) as trans:
            for p in pl:
                c: CharChoice
                c = g.user_input([p], ChooseGirlInputlet(self, mapping), timeout=30, trans=trans)
                c = c or next(_c for _c in choices if not _c.chosen)
                c.chosen = p
                cls = c.char_cls
                assert cls
                banned.add(cls)
                trans.notify('girl_chosen', (p, c))

        assert len(banned) == 4

        chars = [_c for _c in chars if _c not in banned]

        g.random.shuffle(chars)

        if Game.CLIENT:
            chars = [None] * len(chars)

        mapping: Dict[Player, List[CharChoice]] = {}

        for p in pl:
            mapping[p] = [CharChoice(cls) for cls in chars[-4:]]
            mapping[p][-1].akari = True

            del chars[-4:]

            p.reveal(mapping[p])

        g.pause(1)

        with InputTransaction('ChooseGirl', pl, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)

            @ilet.with_post_process
            def process(p, c):
                c = c or mapping[p][0]
                trans.notify('girl_chosen', (p, c))
                return c

            rst = g.user_input(pl, ilet, timeout=30, type='all', trans=trans)

        # reveal
        g.players = BatchList()

        for p in pl:
            c = rst[p]
            c.akari = False
            pl.reveal(c)
            assert c.char_cls
            ch = c.char_cls(p)
            g.players.append(ch)

        g.refresh_dispatcher()

        for p, ch in zip(pl, g.players):
            assert p is ch.player
            g.emit_event('switch_character', (p, ch))

        # -------
        for ch in g.players:
            log.info(
                '>> Player: %s:%s',
                ch.__class__.__name__,
                g.roles[ch.player].get().name,
            )
        # -------

        g.forces = {}
        for ch in g.players:
            g.forces.setdefault(g.roles[ch.player].get(), BatchList()).append(ch)

        g.emit_event('game_begin', g)

        for ch in g.players:
            g.process_action(DistributeCards(ch, amount=4))

        for i, ch in enumerate(cycle(g.players)):
            if i >= 6000: break
            if not ch.dead:
                try:
                    g.process_action(PlayerTurn(ch))
                except InterruptActionFlow:
                    pass

        return True


class THBattle2v2(THBattle):
    n_persons    = 4
    game_ehs     = [
        DeathHandler,
        HeritageHandler,
        ExtraCardHandler,
    ]
    bootstrap    = THBattle2v2Bootstrap
    params_def   = {
        'random_force':    (True, False),
        'draw_extra_card': (False, True),
    }

    forces: Dict[THB2v2Role, BatchList[Character]]

    draw_extra: bool

    def can_leave(g, p: Player):
        for ch in g.players:
            if ch.player is p:
                return ch.dead
        else:
            return False
