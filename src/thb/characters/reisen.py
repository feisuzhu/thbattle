# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import ActionShootdown
from thb.actions import ActionStageLaunchCard, Damage, LaunchCard, PlayerTurn, UserAction
from thb.cards.base import Skill
from thb.cards.classes import AttackCard, DuelCard, Heal, HealCard, PhysicalCard, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class Lunatic(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class Discarder(Skill):
    associated_action = None
    distance = 1
    skill_category = ['character', 'passive']
    target = t_None


class MahjongDrug(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class LunaticAction(UserAction):
    def apply_action(self):
        self.target.skills.append(Discarder)
        self.target.tags['reisen_discarder'] = True  # for tag
        return True


class LunaticHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not src: return act
            if not src.has_skill(Lunatic): return act

            tgt = act.target
            if tgt.dead or tgt.has_skill(Discarder): return act

            g = self.game
            for lc in reversed(g.action_stack):
                if isinstance(lc, LaunchCard):
                    break
            else:
                return act

            c = lc.card
            if not (c.is_card(AttackCard) or c.is_card(DuelCard)):
                return act

            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                g.process_action(LunaticAction(src, tgt))

        return act


class DiscarderAttackOnly(ActionShootdown):
    pass


class DiscarderDistanceLimit(ActionShootdown):
    pass


class DiscarderHandler(THBEventHandler):
    interested = ['action_after', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown' and isinstance(act, ActionStageLaunchCard):
            src = act.source
            if not src.has_skill(Discarder): return act
            g = self.game
            if src is not g.current_player: return act

            self.card = c = act.card
            if not c.is_card(PhysicalCard): return act
            if not c.is_card(AttackCard): raise DiscarderAttackOnly

            dist = LaunchCard.calc_distance(src, Discarder(src))
            dist.pop(src, '')
            nearest = max(min(dist.values()), 0)
            avail = {p for p in dist if dist[p] <= nearest}

            if not set(act.target_list) <= avail:
                raise DiscarderDistanceLimit

        elif evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.has_skill(Discarder):
                tgt.skills.remove(Discarder)
                tgt.tags['reisen_discarder'] = False  # for tag

        return act


class MahjongDrugAction(UserAction):
    def apply_action(self):
        self.target.tags['wine'] = True
        return True

    def is_valid(self):
        return not self.target.dead


class MahjongDrugHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Heal):
            tgt = act.target
            if not tgt.has_skill(MahjongDrug): return act
            card = getattr(act, 'associated_card', None)
            if not card or not card.is_card(HealCard): return act

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                self.game.process_action(MahjongDrugAction(tgt, tgt))

        return act


@register_character_to('common', '-kof')
class Reisen(Character):
    skills = [Lunatic, MahjongDrug]
    eventhandlers = [DiscarderHandler, LunaticHandler, MahjongDrugHandler]
    maxlife = 4


@register_character_to('kof')
class ReisenKOF(Character):
    skills = [Lunatic]
    eventhandlers = [DiscarderHandler, LunaticHandler]
    maxlife = 4
