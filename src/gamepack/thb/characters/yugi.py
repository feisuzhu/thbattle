# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DropCards, FatetellAction
from ..cards import BaseAttack, Card, InevitableAttack, RedUFOSkill, Skill, t_None
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input
from utils import classmix


# -- code --
class AssaultSkill(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


class FreakingPowerSkill(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class FreakingPower(FatetellAction):
    def __init__(self, atkact):
        self.atkact = atkact
        self.source = atkact.source
        self.target = atkact.target
        self.fatetell_target = atkact.target
        self.fatetell_cond = lambda c: c.color == Card.RED

    def fatetell_action(self, ft):
        act = self.atkact
        if ft.succeeded:
            act.__class__ = classmix(InevitableAttack, act.__class__)
        else:
            act.yugifptag = True

        return True


class YugiHandler(EventHandler):
    interested = ('action_after', 'action_before', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack) and not hasattr(act, 'yugifptag'):
            src = act.source
            if not src.has_skill(FreakingPowerSkill): return act
            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act
            tgt = act.target
            Game.getgame().process_action(FreakingPower(act))

        elif evt_type == 'action_after' and hasattr(act, 'yugifptag'):
            if not act.succeeded: return act
            src, tgt = act.source, act.target
            if tgt.dead: return act
            g = Game.getgame()
            catnames = ('cards', 'showncards', 'equips')
            card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
            if card:
                g.players.exclude(tgt).reveal(card)
                g.process_action(DropCards(tgt, [card]))

        return act


@register_character
class Yugi(Character):
    skills = [AssaultSkill, FreakingPowerSkill]
    eventhandlers_required = [YugiHandler]
    maxlife = 4
