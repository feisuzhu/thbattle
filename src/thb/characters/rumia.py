# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING

# -- third party --
# -- own --
from game.base import ActionShootdown
from thb.actions import Damage, DrawCards, FinalizeStage, LaunchCard, UserAction, ttags
from thb.actions import user_choose_cards
from thb.cards.base import PhysicalCard, Skill, t_None, t_OtherN
from thb.cards.basic import Attack
from thb.cards.definition import AttackCard, RejectCard
from thb.cards.spellcard import BaseDuel
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler

# -- typing --
if TYPE_CHECKING:
    from thb.thbkof import THBattleKOF  # noqa: F401


# -- code --
class DarknessDuel(BaseDuel):
    pass


class DarknessAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        attacker, victim = self.target_list
        src = self.source
        g = self.game
        ttags(src)['darkness_tag'] = True

        cards = user_choose_cards(self, attacker, ('cards', 'showncards'))
        if cards:
            c = cards[0]
            g.process_action(LaunchCard(attacker, [victim], c))
        else:
            g.process_action(Damage(src, attacker, 1))

        return True

    def cond(self, cl):
        if len(cl) != 1: return False
        c = cl[0]
        if not c.associated_action: return False
        return issubclass(c.associated_action, Attack)

    def ask_for_action_verify(self, p, cl, tl):
        attacker, victim = self.target_list
        return LaunchCard(attacker, [victim], cl[0]).can_fire()

    def is_valid(self):
        if ttags(self.source)['darkness_tag']:
            return False

        attacker, victim = self.target_list
        if not LaunchCard(attacker, [victim], AttackCard()).can_fire():
            return False

        return True


class Darkness(Skill):
    associated_action = DarknessAction
    skill_category = ['character', 'active']
    target = t_OtherN(2)
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if not(cl and len(cl) == 1):
            return False

        if cl[0].is_card(Skill):
            return False

        return True


class DarknessKOF(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


class DarknessKOFAction(UserAction):
    def apply_action(self):
        tgt = self.target
        ttags(tgt)['darkness_kof_tag'] = True
        return True


class DarknessKOFLimit(ActionShootdown):
    pass


class DarknessKOFHandler(THBEventHandler):
    interested = ['character_debut', 'action_shootdown']
    game: THBattleKOF

    def handle(self, evt_type, arg):
        if evt_type == 'character_debut':
            old, new = arg
            if new.has_skill(DarknessKOF):
                g = self.game
                g.process_action(DarknessKOFAction(new, new))

        elif evt_type == 'action_shootdown' and isinstance(arg, LaunchCard):
            src = arg.source
            if not src:
                return arg

            g = self.game
            opp = g.get_opponent(arg.source)
            if ttags(opp)['darkness_kof_tag']:
                return arg

            card = arg.card
            if not card.is_card(PhysicalCard) and 'treat_as' not in card.category:
                return arg

            if card.is_card(RejectCard):
                return arg

            # XXX: DollControl's second target do not count as target
            # but in KOF the second target is always the launcher,
            # and never be the opp, so the handle can be same.
            if opp in arg.target_list:
                raise DarknessKOFLimit

        return arg


class Cheating(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None()


class CheatingDrawCards(DrawCards):
    pass


class CheatingHandler(THBEventHandler):
    interested = ['action_apply']
    execute_before = ['CiguateraHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            tgt = act.target
            if tgt.has_skill(Cheating) and not tgt.dead:
                g = self.game
                g.process_action(CheatingDrawCards(tgt, 1))
        return act


@register_character_to('common', '-kof')
class Rumia(Character):
    skills = [Darkness, Cheating]
    eventhandlers = [CheatingHandler]
    maxlife = 3


@register_character_to('kof')
class RumiaKOF(Character):
    skills = [DarknessKOF, Cheating]
    eventhandlers = [DarknessKOFHandler, CheatingHandler]
    maxlife = 3
