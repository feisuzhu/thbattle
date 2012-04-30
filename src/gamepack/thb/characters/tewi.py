# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Luck(Skill):
    associated_action = None
    target = t_None

class LuckDrawCards(DrawCards):
    pass

class LuckHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after':
            for p in [getattr(act, 'source', None), getattr(act, 'target', None)]:
                if p and p.has_skill(Luck) and not (p.cards or p.showncards):
                    Game.getgame().process_action(LuckDrawCards(p, 2))
                    
        elif evt_type == 'action_apply' and isinstance(act, LaunchCard):
            p = act.source
            if p and p.has_skill(Luck) and (len(p.cards) + len(p.showncards)) == 1:
                Game.getgame().process_action(LuckDrawCards(p, 2))
        return act

@register_character
class Tewi(Character):
    skills = [Luck]
    eventhandlers_required = [LuckHandler]
    maxlife = 3
