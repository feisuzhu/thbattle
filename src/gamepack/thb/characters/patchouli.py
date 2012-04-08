# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..skill import *
from ..cards import *

class Library(Skill):
    associated_action = None
    target = t_None

class Knowledge(Skill):
    associated_action = None
    target = t_None

class PatchouliHandler(EventHandler):
    execute_before = (RejectHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            src = act.source
            tgt = act.target
            if src.has_skill(Library):
                Game.getgame().process_action(DrawCards(src, 1))

            if tgt.has_skill(Knowledge):
                c = getattr(act, 'associated_card', None)
                if c and c.suit == Card.SPADE:
                    act.cancelled = True
        return act

@register_character
class Patchouli(Character):
    skills = [Library, Knowledge]
    eventhandlers_required = [PatchouliHandler]
    maxlife = 3
