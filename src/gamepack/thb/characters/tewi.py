# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..skill import *
from ..cards import *

class Luck(Skill):
    associated_action = None
    target = t_None

class LuckHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after':
            for p in [getattr(act, 'source', None), getattr(act, 'target', None)]:
                if p and p.has_skill(Luck) and not (p.cards or p.showncards):
                    g = Game.getgame()
                    g.process_action(DrawCards(p, 2))
        return act

@register_character
class Tewi(Character):
    skills = [Luck]
    eventhandlers_required = [LuckHandler]
    maxlife = 3
