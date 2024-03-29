# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionLimitExceeded, ActionShootdown, DrawCards, LaunchCard, Pindian
from thb.actions import PrepareStage, UserAction
from thb.cards.base import Skill, VirtualCard
from thb.cards.classes import AttackCard, TreatAs, WineCard, t_None, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler


# -- code --
class HeavyDrinkerWine(TreatAs, VirtualCard):
    treat_as = WineCard


class HeavyDrinkerFailed(ActionShootdown):
    pass


class HeavyDrinkerAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        src.tags['suika_target'].append(tgt)
        if g.process_action(Pindian(src, tgt)):
            g.process_action(LaunchCard(src, [src], HeavyDrinkerWine(src), bypass_check=True))
            g.process_action(LaunchCard(tgt, [tgt], HeavyDrinkerWine(src), bypass_check=True))

        else:
            src.tags['suika_failed'] = src.tags['turn_count']

        return True

    def is_valid(self):
        tags = self.source.tags
        if tags['suika_failed'] >= tags['turn_count']:
            raise HeavyDrinkerFailed

        if self.target in tags['suika_target']:
            raise ActionLimitExceeded

        Pindian(self.source, self.target).action_shootdown_exception()

        return True


class HeavyDrinker(Skill):
    skill_category = ['character', 'active']
    associated_action = HeavyDrinkerAction
    target = t_OtherOne()

    def check(self):
        return not self.associated_cards


class HeavyDrinkerHandler(THBEventHandler):
    interested = ['action_apply']
    execute_before = ['WineHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PrepareStage):
            act.target.tags['suika_target'] = []

        return act


class DrunkenDream(Skill):
    target = t_None()
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']


class DrunkenDreamDrawCards(DrawCards):
    pass


class DrunkenDreamHandler(THBEventHandler):
    interested = ['action_apply', 'calcdistance']
    execute_before = ['WineHandler']

    def handle(self, evt_type, act):
        if evt_type == 'calcdistance':
            src, card, dist = act
            if card.is_card(AttackCard):
                if not src.has_skill(DrunkenDream):
                    return act

                if not src.tags['wine']:
                    return act

                for p in dist:
                    dist[p] -= 2

        elif evt_type == 'action_apply' and isinstance(act, PrepareStage):
            tgt = act.target
            if not tgt.has_skill(DrunkenDream):
                return act

            if not tgt.tags['wine']:
                return act

            g = self.game
            g.process_action(DrunkenDreamDrawCards(tgt, 1))

        return act


@register_character_to('common')
class Suika(Character):
    skills = [HeavyDrinker, DrunkenDream]
    eventhandlers = [
        HeavyDrinkerHandler,
        DrunkenDreamHandler,
    ]
    maxlife = 4
