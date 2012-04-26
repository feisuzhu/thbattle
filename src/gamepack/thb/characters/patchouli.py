# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Library(Skill):
    associated_action = None
    target = t_None

class Knowledge(Skill):
    associated_action = None
    target = t_None

class LibraryDrawCard(DrawCards):
    pass

class KnowledgeAction(GenericAction):
    def __init__(self, act):
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True

class PatchouliHandler(EventHandler):
    execute_before = (RejectHandler, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, InstantSpellCardAction):
            src = act.source
            tgt = act.target
            if src.has_skill(Library):
                Game.getgame().process_action(LibraryDrawCards(src, 1))

            if tgt.has_skill(Knowledge):
                c = getattr(act, 'associated_card', None)
                if c and c.suit == Card.SPADE:
                    Game.getgame().process_action(KnowledgeAction(act))
        return act

@register_character
class Patchouli(Character):
    skills = [Library, Knowledge]
    eventhandlers_required = [PatchouliHandler]
    maxlife = 3
