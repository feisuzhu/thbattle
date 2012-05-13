# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class DarknessDuel(BaseDuel):
    pass

class DarknessAction(UserAction):
    def apply_action(self):
        tl = self.target_list
        g = Game.getgame()
        tags = self.source.tags
        tags['darkness_tag'] = tags['turn_count']
        g.process_action(DarknessDuel(tl[1], tl[0]))
        return True

    def is_valid(self):
        tags = self.source.tags
        if tags['turn_count'] <= tags['darkness_tag']:
            return False
        return True

class Darkness(Skill):
    associated_action = DarknessAction
    target = t_OtherN(2)
    def check(self):
        cl = self.associated_cards
        return cl and len(cl) == 1

class Cheating(Skill):
    associated_action = None
    target = t_None

class CheatingDrawCards(DrawCards):
    pass

class CheatingHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.has_skill(Cheating) and not tgt.dead:
                g = Game.getgame()
                g.process_action(CheatingDrawCards(tgt, 1))
        return act

@register_character
class Rumia(Character):
    skills = [Darkness, Cheating]
    eventhandlers_required = [CheatingHandler]
    maxlife = 3
