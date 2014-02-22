# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, GenericAction
from ..cards import Card, Skill, RejectCard, SpellCardAction, t_None


class Library(Skill):
    associated_action = None
    target = t_None


class Knowledge(Skill):
    associated_action = None
    target = t_None


class LibraryDrawCards(DrawCards):
    pass


class KnowledgeAction(GenericAction):
    def __init__(self, act):
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True


class PatchouliHandler(EventHandler):
    execute_before = ('RejectHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'choose_target':
            act, tl = arg = act
            src = act.source

            if not src.has_skill(Library):
                return arg

            if 'instant_spellcard' in act.card.category:
                Game.getgame().process_action(LibraryDrawCards(src, 1))

            return arg

        if evt_type == 'action_before':

            if isinstance(act, SpellCardAction) and not act.cancelled:
                tgt = act.target
                if tgt.has_skill(Knowledge):
                    c = getattr(act, 'associated_card', None)
                    if c and c.suit == Card.SPADE and not c.is_card(RejectCard):
                        Game.getgame().process_action(KnowledgeAction(act))

        return act


@register_character
class Patchouli(Character):
    skills = [Library, Knowledge]
    eventhandlers_required = [PatchouliHandler]
    maxlife = 3
