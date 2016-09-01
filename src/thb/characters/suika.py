# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from thb.actions import ActionLimitExceeded, ActionShootdown, ActionStage, DrawCards, LaunchCard
from thb.actions import Pindian, PlayerTurn, UserAction
from thb.cards import AttackCard, Skill, TreatAs, VirtualCard, WineCard, t_None, t_OtherOne
from thb.characters.baseclasses import Character, register_character_to


# -- code --
class HeavyDrinkerWine(TreatAs, VirtualCard):
    treat_as = WineCard


class HeavyDrinkerFailed(ActionShootdown):
    pass


class HeavyDrinkerAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
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
    skill_category = ('character', 'active')
    associated_action = HeavyDrinkerAction
    target = t_OtherOne

    def check(self):
        return not self.associated_cards


class HeavyDrinkerHandler(EventHandler):
    interested = ('action_apply', )
    execute_before = ('WineHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            act.target.tags['suika_target'] = []

        return act


class DrunkenDream(Skill):
    target = t_None
    associated_action = None
    skill_category = ('character', 'passive')


class DrunkenDreamDrawCards(DrawCards):
    pass


class DrunkenDreamHandler(EventHandler):
    interested = ('action_apply', 'calcdistance')
    execute_before = ('WineHandler', )

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

        elif evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            src = act.source
            if not src.has_skill(DrunkenDream):
                return act

            if not src.tags['wine']:
                return act

            g = Game.getgame()
            g.process_action(DrunkenDreamDrawCards(src, 1))

        return act


@register_character_to('common')
class Suika(Character):
    skills = [HeavyDrinker, DrunkenDream]
    eventhandlers_required = [
        HeavyDrinkerHandler,
        DrunkenDreamHandler,
    ]
    maxlife = 4
