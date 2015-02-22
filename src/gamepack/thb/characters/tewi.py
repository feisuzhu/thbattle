# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards
from ..cards import Skill, t_None
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class Luck(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class LuckDrawCards(DrawCards):
    pass


class LuckHandler(EventHandler):
    interested = ('card_migration',)
    def handle(self, evt_type, arg):
        if evt_type != 'card_migration':
            return arg

        act, l, _from, to = arg  # (action, cardlist, from, to)
        p = _from.owner

        if p and p.has_skill(Luck) and not p.dead:
            if _from not in (p.cards, p.showncards):
                return arg

            if not (p.cards or p.showncards):
                Game.getgame().process_action(LuckDrawCards(p, 2))

        return arg


@register_character
class Tewi(Character):
    skills = [Luck]
    eventhandlers_required = [LuckHandler]
    maxlife = 4
