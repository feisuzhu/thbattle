# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from copy import copy
from enum import Enum
from itertools import cycle
from typing import Any, Dict, List
import logging
import random

# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import BootstrapAction, GameEnded, GameItem, InputTransaction, InterruptActionFlow
from game.base import Player, get_seed_for, sync_primitive
from thb.actions import ActionStageLaunchCard, AskForCard, DistributeCards, DrawCards, DropCardStage
from thb.actions import DropCards, GenericAction, LifeLost, PlayerDeath, PlayerTurn, RevealRole
from thb.actions import TryRevive, UserAction, ask_for_action, ttags
from thb.cards.base import Card, Deck, Skill, VirtualCard
from thb.cards.classes import AttackCard, AttackCardRangeHandler, GrazeCard, Heal, TreatAs, t_None
from thb.cards.classes import t_One
from thb.common import CharChoice, PlayerRole, build_choices
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet
from thb.item import ImperialRole
from thb.mode import THBEventHandler, THBattle
from utils.misc import BatchList, classmix


# -- code --
log = logging.getLogger('THBattleIdentity')


class RoleRevealHandler(THBEventHandler):
    interested = ['action_apply']
    execute_before = ['DeathHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = self.game
            tgt = act.target

            g.process_action(RevealRole(tgt.player, g.players.player))

        return act


class DeathHandler(THBEventHandler):
    interested = ['action_apply', 'action_after']
    game: 'THBattleRole'

    def handle(self, evt_type: str, act) -> Any:
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = self.game
            T = THBRoleRole
            pl = g.players.player

            tgt = act.target
            dead = lambda p: p.dead or p is tgt

            # curtain's win
            survivors = [p for p in g.players if not dead(p)]
            if len(survivors) == 1:
                pl.reveal([g.roles[p] for p in pl])

                if g.roles[survivors[0].player] == T.CURTAIN:
                    raise GameEnded([survivors[0].player])

            deads: Dict[THBRoleRole, int] = defaultdict(int)
            for p in g.players:
                if dead(p):
                    deads[g.roles[p.player].get()] += 1

            def winner(*roles: THBRoleRole):
                pl.reveal([g.roles[p] for p in pl])

                raise GameEnded([
                    p for p in pl
                    if g.roles[p].get() in roles
                ])

            def has_no(i: THBRoleRole):
                return deads[i] == g.roles_config.count(i)

            # attackers' & curtain's win
            if deads[T.BOSS]:
                if g.double_curtain:
                    winner(T.ATTACKER)
                else:
                    if has_no(T.ATTACKER):
                        winner(T.CURTAIN)
                    else:
                        winner(T.ATTACKER)

            # boss & accomplices' win
            if has_no(T.ATTACKER) and has_no(T.CURTAIN):
                winner(T.BOSS, T.ACCOMPLICE)

            # all survivors dropped
            if all([g.is_dropped(ch.player) for ch in survivors]):
                pl.reveal([g.roles[p] for p in pl])
                raise GameEnded([])

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            T = THBRoleRole
            g = self.game
            tgt = act.target
            src = act.source

            if not src:
                return act

            if g.roles[tgt.player] == T.ATTACKER:
                g.process_action(DrawCards(src, 3))
            elif g.roles[tgt.player] == T.ACCOMPLICE:
                if g.roles[src.player] == T.BOSS:
                    pl.exclude(src.player).reveal(list(src.cards))

                    cards: List[Card] = []
                    cards.extend(src.cards)
                    cards.extend(src.showncards)
                    cards.extend(src.equips)
                    cards and g.process_action(DropCards(src, src, cards))

        return act


class AssistedAttackCard(TreatAs, VirtualCard):
    treat_as = AttackCard


class AssistedAttackAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        pl = [p for p in g.players if not p.dead and p is not src]
        p, rst = ask_for_action(self, pl, ('cards', 'showncards'), [], timeout=6)
        if not p:
            ttags(src)['assisted_attack_disable'] = True
            return False

        assert rst

        (c,), _ = rst
        g.process_action(ActionStageLaunchCard(src, [tgt], AssistedAttackCard.wrap([c], src)))

        return True

    def cond(self, cl):
        return len(cl) == 1 and cl[0].is_card(AttackCard)

    def is_valid(self):
        src, tgt = self.source, self.target
        act = ActionStageLaunchCard(src, [tgt], AttackCard())
        disabled = ttags(src)['assisted_attack_disable']
        return not disabled and act.can_fire()


class AssistedAttack(Skill):
    associated_action = AssistedAttackAction
    target = t_One
    skill_category = ['character', 'active', 'boss']
    distance = 1

    def check(self):
        return not self.associated_cards


class AssistedGraze(Skill):
    associated_action = None
    target = t_None
    skill_category = ['character', 'passive', 'boss']


class DoNotProcessCard(object):

    def process_card(self, c):
        return True


class AssistedUseAction(UserAction):
    def __init__(self, target, afc):
        self.source = self.target = target
        self.their_afc_action = afc

    def apply_action(self):
        tgt = self.target
        g = self.game

        pl = BatchList([p for p in g.players if not p.dead])
        pl = pl.rotate_to(tgt)[1:]
        rst = user_input(pl, ChooseOptionInputlet(self, (False, True)), timeout=6, type='all')

        afc = self.their_afc_action
        for p in pl:
            if p in rst and rst[p]:
                act = copy(afc)
                act.__class__ = classmix(DoNotProcessCard, afc.__class__)
                act.target = p
                if g.process_action(act):
                    self.their_afc_action.card = act.card
                    return True
        else:
            return False

        return True


class AssistedUseHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, AskForCard):
            tgt = act.target
            if not (tgt.has_skill(self.skill) and issubclass(act.card_cls, self.card_cls)):
                return act

            if isinstance(act, DoNotProcessCard):
                return act

            self.assist_target = tgt
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g = self.game
            g.process_action(AssistedUseAction(tgt, act))

        return act


class AssistedAttackHandler(AssistedUseHandler):
    skill = AssistedAttack
    card_cls = AttackCard


class AssistedAttackRangeHandler(AssistedUseHandler):
    interested = ['calcdistance']

    def handle(self, evt_type, arg):
        src, card, dist = arg
        if evt_type == 'calcdistance':
            if card.is_card(AssistedAttack):
                AttackCardRangeHandler.fix_attack_range(src, dist)

        return arg


class AssistedGrazeHandler(AssistedUseHandler):
    skill = AssistedGraze
    card_cls = GrazeCard


class AssistedHealAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        g.process_action(Heal(src, tgt))
        g.process_action(LifeLost(src, src))
        return True


class AssistedHealHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, TryRevive):
            if not act.succeeded:
                return act

            assert act.revived_by

            tgt = act.target
            if not tgt.has_skill(AssistedHeal):
                return act

            self.good_person = p = act.revived_by  # for ui

            if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                return act

            g = self.game
            g.process_action(AssistedHealAction(p, tgt))

        return act


class AssistedHeal(Skill):
    associated_action = None
    target = t_None
    skill_category = ['character', 'passive', 'boss']


class ExtraCardSlotHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if not tgt.has_skill(ExtraCardSlot):
                return act

            g = self.game
            n = sum(i == THBRoleRole.ACCOMPLICE for i in g.roles)
            n -= sum(p.dead and p.identity.type == THBRoleRole.ACCOMPLICE for p in g.players)
            act.dropn = max(act.dropn - n, 0)

        return act


class ExtraCardSlot(Skill):
    associated_action = None
    target = t_None
    skill_category = ['character', 'passive', 'boss']


class THBRoleRole(Enum):
    HIDDEN     = 0
    ATTACKER   = 1
    BOSS       = 4
    ACCOMPLICE = 2
    CURTAIN    = 3


class ChooseBossSkillAction(GenericAction):
    def apply_action(self) -> bool:
        tgt = self.target

        if tgt.boss_skills:
            bs = tgt.boss_skills
            assert len(bs) == 1
            tgt.skills.extend(bs)
            self.skill_chosen = bs[0]
            return True

        self.boss_skills = lst = [  # for ui
            AssistedAttack,
            AssistedGraze,
            AssistedHeal,
            ExtraCardSlot,
        ]
        rst = user_input([tgt], ChooseOptionInputlet(self, [i.__name__ for i in lst]))
        rst = next((i for i in lst if i.__name__ == rst), None) or next(iter(lst))
        tgt.skills.append(rst)
        self.skill_chosen = rst  # for ui
        return True


class THBattleRoleBootstrap(BootstrapAction):
    game: 'THBattleRole'

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

        g.deck = Deck(g)

        # arrange roles -->
        g.double_curtain = params['double_curtain']

        B = THBRoleRole.BOSS
        T = THBRoleRole.ATTACKER
        A = THBRoleRole.ACCOMPLICE
        C = THBRoleRole.CURTAIN

        if g.double_curtain:
            roles = [B, T, T, T, A, A, C, C]
        else:
            roles = [B, T, T, T, T, A, A, C]

        orig_pl = self.players
        pl = BatchList[Player](orig_pl)

        g.roles_config = roles[:]

        imperial_roles = ImperialRole.get_chosen(self.items, pl)
        for p, i in imperial_roles:
            pl.remove(p)
            roles.remove(i)

        g.random.shuffle(roles)

        if g.CLIENT:
            roles = [THBRoleRole.HIDDEN for _ in roles]

        g.roles = {}

        for p, i in imperial_roles + list(zip(pl, roles)):
            g.roles[p] = PlayerRole(THBRoleRole)
            g.roles[p].set(i)
            g.process_action(RevealRole(p, p))

        del roles

        is_boss = sync_primitive([g.roles[p] == THBRoleRole.BOSS for p in pl], pl)
        boss_idx = is_boss.index(True)
        boss = g.boss = pl[boss_idx]

        g.process_action(RevealRole(boss, pl))

        # choose girls init -->
        from .characters import get_characters
        pl = pl.rotate_to(boss)

        choices, _ = build_choices(
            g, pl, self.items,
            candidates=get_characters('common', 'id', 'id8', '-boss'),
            spec={boss: {'num': 5, 'akaris': 1}},
        )

        choices[boss][:0] = [CharChoice(cls) for cls in get_characters('boss')]

        with InputTransaction('ChooseGirl', [boss], mapping=choices) as trans:
            c: CharChoice = user_input([boss], ChooseGirlInputlet(g, choices), 30, 'single', trans)

            c = c or choices[boss][-1]
            c.chosen = boss
            c.akari = False
            pl.reveal(c)
            trans.notify('girl_chosen', (boss, c))
            assert c.char_cls

        chars = get_characters('common', 'id', 'id8')

        try:
            chars.remove(c.char_cls)
        except Exception:
            pass

        g.players = BatchList()

        # mix it in advance
        # so the others could see it

        boss_ch = c.char_cls(boss)
        g.players.append(boss_ch)
        g.emit_event('switch_character', (None, boss_ch))

        # boss's hp bonus
        boss_ch.maxlife += 1
        boss_ch.life = boss_ch.maxlife

        # choose boss dedicated skill
        g.process_action(ChooseBossSkillAction(boss_ch, boss_ch))

        # reseat
        seed = get_seed_for(g, pl)
        random.Random(seed).shuffle(pl)
        g.emit_event('reseat', (orig_pl, pl))

        # others choose girls
        pl_wo_boss = pl.exclude(boss)

        choices, _ = build_choices(
            g, pl, self.items,
            candidates=chars,
            spec={p: {'num': 4, 'akaris': 1} for p in pl_wo_boss},
        )

        with InputTransaction('ChooseGirl', pl_wo_boss, mapping=choices) as trans:
            ilet = ChooseGirlInputlet(g, choices)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            result = user_input(pl_wo_boss, ilet, type='all', trans=trans)

        # mix char class with player -->
        for p in pl_wo_boss:
            c = result[p] or choices[p][-1]
            c.akari = False
            pl.reveal(c)
            assert c.char_cls
            ch = c.char_cls(p)
            g.players.append(ch)
            g.emit_event('switch_character', (None, ch))

        assert g.players.player == pl

        # -------
        for ch in g.players:
            log.info(
                '>> Player: %s:%s %s',
                ch.__class__.__name__,
                g.roles[ch.player].get().name,
                g.name_of(ch.player),
            )
        # -------

        g.refresh_dispatcher()
        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=4))

        for i, p in enumerate(cycle(g.players.rotate_to(boss_ch))):
            if i >= 6000: break
            if not p.dead:
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        return True


class THBattleRole(THBattle):
    n_persons = 8
    game_ehs = [
        RoleRevealHandler,
        DeathHandler,
        AssistedAttackHandler,
        AssistedAttackRangeHandler,
        AssistedGrazeHandler,
        AssistedHealHandler,
        ExtraCardSlotHandler,
    ]
    bootstrap = THBattleRoleBootstrap
    params_def = {
        'double_curtain': (False, True),
    }

    # ----- instance vars -----
    boss: Player
    roles_config: List[THBRoleRole]
    double_curtain: bool

    def can_leave(self, p):
        return p.dead
