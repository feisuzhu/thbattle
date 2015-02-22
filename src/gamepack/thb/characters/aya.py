# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards, PlayerTurn, UserAction
from ..cards import Skill, t_None
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler, Game


# -- code --
class UltimateSpeed(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class UltimateSpeedAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        return g.process_action(DrawCards(self.target, 1))


class UltimateSpeedHandler(EventHandler):
    interested = ('action_apply', 'choose_target', 'post_calcdistance')
    def handle(self, evt_type, arg):
        def is_card(card):
            return 'skill' not in card.category or 'treat_as' in card.category

        if evt_type == 'post_calcdistance':
            src, card, dist = arg

            if not is_card(card):
                return arg

            if src.tags['aya_count'] < 2:
                return arg

            g = Game.getgame()
            if g.current_turn is not src:
                return arg

            for k in dist:
                dist[k] = 0

        elif evt_type == 'action_apply' and isinstance(arg, PlayerTurn):
            tags = arg.target.tags
            tags['aya_count'] = 0
            tags['aya_range_max'] = False

        elif evt_type == 'choose_target':
            lca, _ = arg
            g = Game.getgame()

            if not is_card(lca.card):
                return arg

            src = lca.source

            if not src.has_skill(UltimateSpeed): return arg

            # if not isinstance(lca, ActionStageLaunchCard):
            if g.current_turn is not src:
                return arg

            src.tags['aya_count'] += 1
            if src.tags['aya_count'] == 2:
                g.process_action(UltimateSpeedAction(src, src))

        return arg


@register_character_to('common')
class Aya(Character):
    skills = [UltimateSpeed]
    eventhandlers_required = [UltimateSpeedHandler]
    maxlife = 4
