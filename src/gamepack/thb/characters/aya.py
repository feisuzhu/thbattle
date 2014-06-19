# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import PlayerTurn, DrawCards, UserAction
from ..inputlets import ChooseOptionInputlet
from ..cards import Skill, VirtualCard, TreatAsSkill, t_None


class UltimateSpeedAction(UserAction):
    def apply_action(self):
        self.target.tags['aya_range_max'] = False
        return True


class UltimateSpeed(Skill):
    associated_action = None
    target = t_None


class UltimateSpeedHandler(EventHandler):
    def handle(self, evt_type, arg):
        def is_card(card):
            return not card.is_card(VirtualCard) or card.is_card(TreatAsSkill)

        if evt_type == 'post_calcdistance':
            src, card, dist = arg
            if not is_card(card): return arg
            if not src.tags.get('aya_range_max'): return arg

            g = Game.getgame()
            if g.current_turn is not src: return arg

            for k in dist: dist[k] = 0

        elif evt_type == 'action_apply' and isinstance(arg, PlayerTurn):
            tags = arg.target.tags
            tags['aya_count'] = 0
            tags['aya_range_max'] = False
            

        elif evt_type == 'choose_target':
            lca, _ = arg
            g = Game.getgame()

            if not is_card(lca.card): return arg
            src = lca.source
            if src.tags.get('aya_range_max'):
                g.process_action(UltimateSpeedAction(src, src))

            if not src.has_skill(UltimateSpeed): return arg
            
            #if not isinstance(lca, ActionStageLaunchCard):
            if g.current_turn is not src:
                return arg

            src.tags['aya_count'] += 1
            if src.tags['aya_count'] % 2 == 0:
                opt = user_input([src],
                    ChooseOptionInputlet(self, (None, 'draw', 'range'))
                )
                if opt == 'draw':
                    g.process_action(DrawCards(src, 1))
                
                elif opt == 'range':
                    src.tags['aya_range_max'] = True

        return arg


@register_character
class Aya(Character):
    skills = [UltimateSpeed]
    eventhandlers_required = [UltimateSpeedHandler]
    maxlife = 4
