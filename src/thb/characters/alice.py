# -*- coding: utf-8 -*-

from typing import Sequence, Tuple, List
# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionStage, Damage, DrawCards, DropCardStage, DropCards, GenericAction
from thb.actions import LaunchCard, PlayerTurn, PostCardMigrationHandler, Reforge, UserAction
from thb.actions import random_choose_card, user_choose_cards, user_choose_players
from thb.cards.base import Skill, VirtualCard
from thb.cards.definition import EquipmentCard
from thb.cards.classes import AttackCard, DollControlCard, Heal, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class LittleLegionAttackCard(TreatAs, VirtualCard):
    treat_as = AttackCard


class LittleLegionDollControlCard(TreatAs, VirtualCard):
    treat_as = DollControlCard


class LittleLegion(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class LittleLegionAttackAction(UserAction):
    def apply_action(self):
        g = self.game
        src = self.source
        pl = [p for p in g.players if not p.dead and p is not src]
        if not pl:
            return False

        victim, = user_choose_players(self, src, pl) or (None,)
        if victim is None:
            return False

        lc = LaunchCard(src, [victim], LittleLegionAttackCard(src), bypass_check=True)
        g.process_action(lc)
        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class LittleLegionCoverEffect(Heal):
    pass


class LittleLegionCoverAction(UserAction):
    def apply_action(self):
        g = self.game
        src = self.source
        pl = [p for p in g.players if not p.dead and p.life < p.maxlife]
        if not pl:
            return False

        beneficiary, = user_choose_players(self, src, pl) or (None,)
        if beneficiary is None:
            return False

        g.process_action(LittleLegionCoverEffect(src, beneficiary, 1))
        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class LittleLegionHoldAction(UserAction):
    def apply_action(self):
        src = self.source

        g = self.game
        g.process_action(DrawCards(src, 1))

        turn = PlayerTurn.get_current(g)
        try:
            turn.pending_stages.remove(DropCardStage)
        except Exception:
            pass

        return True


class LittleLegionControlAction(UserAction):
    def apply_action(self) -> bool:
        g = self.game
        src = self.source
        pl = [p for p in g.players if not p.dead]
        rst = user_choose_players(self, src, pl)

        if not rst:
            return False

        attacker, victim = rst
        self.target_list = attacker, victim

        g.process_action(LaunchCard(src, [attacker, victim], LittleLegionDollControlCard(attacker)))
        return True

    def choose_player_target(self, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        src = self.source
        trimmed, rst = DollControlCard.target(None, None, src, tl)
        return trimmed, rst and LaunchCard(src, trimmed, LittleLegionDollControlCard(src)).can_fire()


class LittleLegionHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStage):
            tgt = act.target
            if not tgt.has_skill(LittleLegion):
                return act

            c, = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips')) or (None,)
            if c is None:
                return act

            g = self.game

            assert isinstance(c, EquipmentCard)
            category = c.equipment_category

            g.process_action(Reforge(tgt, tgt, c))

            if tgt.dead:
                return act

            if category == 'weapon':
                g.process_action(LittleLegionAttackAction(tgt, tgt))
            elif category == 'shield':
                g.process_action(LittleLegionCoverAction(tgt, tgt))
            elif category == 'accessories':
                g.process_action(LittleLegionHoldAction(tgt, tgt))
            elif category in ('redufo', 'greenufo'):
                g.process_action(LittleLegionControlAction(tgt, tgt))

        return act

    def cond(self, cl):
        if len(cl) != 1:
            return False

        c, = cl
        if c.is_card(VirtualCard):
            return False

        return 'equipment' in c.category


class DollBlast(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class DollBlastEffect(GenericAction):
    def __init__(self, source, target, card, do_damage):
        self.source    = source
        self.target    = target
        self.card      = card
        self.do_damage = do_damage

    def apply_action(self):
        g = self.game
        src, tgt = self.source, self.target
        g.process_action(DropCards(src, tgt, [self.card]))
        if self.do_damage:
            g.process_action(Damage(src, tgt, 1))

        return True


class DollBlastAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards  = cards

    def apply_action(self):
        g = self.game
        cl = self.cards
        track_ids = {c.track_id for c in cl}

        src, tgt = self.source, self.target
        for c in cl:
            c = g.user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
            c = c or random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
            if not c: return True
            g.players.reveal(c)
            g.process_action(DollBlastEffect(src, tgt, c, c.track_id in track_ids))

        return True


class DollBlastHandlerCommon(object):

    def fire(self, src, tgt, cards):
        self.target = tgt  # for ui

        g = self.game
        if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
            return

        g.process_action(DollBlastAction(src, tgt, cards))


class DollBlastMigrationHandler(DollBlastHandlerCommon, THBEventHandler):
    interested = ['post_card_migration']
    arbiter = PostCardMigrationHandler

    def handle(self, p, trans):
        if not p.has_skill(DollBlast):
            return True

        equips = p.equips

        for cl, _from, to, is_bh in trans.get_movements():
            if _from is not equips:
                continue

            if to is None or not to.owner:
                continue

            tgt = to.owner

            if tgt is _from.owner:
                continue

            if not (tgt.cards or tgt.showncards or tgt.equips):
                continue

            self.fire(p, tgt, cl)

        return True


class DollBlastDropHandler(DollBlastHandlerCommon, THBEventHandler):
    interested = ['action_before', 'action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCards):
            src, tgt = act.source, act.target

            if not tgt.has_skill(DollBlast):
                return act

            if not src or src is tgt or not (src.cards or src.showncards or src.equips):
                return act

            if not any(c.resides_in.type == 'equips' for c in act.cards):
                return act

            act._['doll_blast'] = True

        elif evt_type == 'action_after' and isinstance(act, DropCards) and act._['doll_blast']:
            self.fire(act.target, act.source, act.cards)

        return act


@register_character_to('common')
class Alice(Character):
    skills = [DollBlast, LittleLegion]
    eventhandlers = [
        DollBlastMigrationHandler,
        DollBlastDropHandler,
        LittleLegionHandler,
    ]
    maxlife = 4
