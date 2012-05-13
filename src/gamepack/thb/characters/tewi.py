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
    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, l, _from, to = arg # (action, cardlist, from, to)
            p = _from.owner
            if p and p.has_skill(Luck) and not p.dead and not (p.cards or p.showncards):
                Game.getgame().process_action(LuckDrawCards(p, 2))
        return arg

@register_character
class Tewi(Character):
    skills = [Luck]
    eventhandlers_required = [LuckHandler]
    maxlife = 4
