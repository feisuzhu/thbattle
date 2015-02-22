# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards, GenericAction
from ..cards import Card, RejectCard, Skill, SpellCardAction, t_None
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class Library(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class Knowledge(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
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


class KnowledgeHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('RejectHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction) and not act.cancelled:
            tgt = act.target
            if tgt.has_skill(Knowledge):
                c = getattr(act, 'associated_card', None)
                if c and c.suit == Card.SPADE and not c.is_card(RejectCard):
                    Game.getgame().process_action(KnowledgeAction(act))

        return act


class LibraryHandler(EventHandler):
    interested = ('action_before', 'calcdistance', 'choose_target')
    execute_before = ('RejectHandler',)

    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            act, tl = arg
            src = act.source

            if not src.has_skill(Library):
                return arg

            if 'instant_spellcard' in act.card.category:
                Game.getgame().process_action(LibraryDrawCards(src, 1))

            return arg

        # elif evt_type == 'action_before' and isinstance(arg, Reject):
        #     act = arg.target_act
        #     src = act.source
        #     if arg.source is src: return arg
        #     if not src.has_skill(Library): return arg

        #     Game.getgame().process_action(LibraryDrawCards(src, 1))

        #     return arg

        elif evt_type == 'calcdistance':
            src, card, dist = arg
            if not src.has_skill(Library): return arg
            if 'spellcard' not in card.category: return arg
            for p in dist:
                dist[p] -= 10000

        return arg


@register_character
class Patchouli(Character):
    skills = [Library, Knowledge]
    eventhandlers_required = [LibraryHandler, KnowledgeHandler]
    maxlife = 3
