# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, PlayerRevive
from ..cards import Skill, t_None


class Luck(Skill):
    associated_action = None
    target = t_None


class LuckDrawCards(DrawCards):
    pass


class LuckHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, l, _from, to = arg  # (action, cardlist, from, to)
            p = _from.owner
        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            p = arg.target
        elif evt_type == 'before_launch_card':
            p = arg.source
        else:
            p = None

        if p and p.has_skill(Luck) and not p.dead:
            if not (p.cards or p.showncards):
                Game.getgame().process_action(LuckDrawCards(p, 2))
        return arg


@register_character
class Tewi(Character):
    skills = [Luck]
    eventhandlers_required = [LuckHandler]
    maxlife = 4
