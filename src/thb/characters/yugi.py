# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import Damage, DropCards, FatetellAction, LaunchCard, mark, marked
from thb.cards import AttackCard, BaseAttack, Card, InevitableAttack, RedUFOSkill, Skill
from thb.cards import TreatAs, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from utils import classmix


# -- code --
class Assault(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


class AssaultKOF(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class AssaultAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class AssaultKOFHandler(EventHandler):
    interested = ('character_debut', )

    def handle(self, evt_type, arg):
        if evt_type == 'character_debut':
            old, new = arg
            if not new.has_skill(AssaultKOF):
                return arg

            g = Game.getgame()
            op = g.get_opponent(new)
            lc = LaunchCard(new, [op], AssaultAttack(new))
            if not lc.can_fire():
                return arg

            if user_input([new], ChooseOptionInputlet(self, (False, True))):
                g.process_action(lc)

        return arg


class FreakingPower(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class FreakingPowerAction(FatetellAction):
    def __init__(self, atkact):
        self.atkact = atkact
        self.source = atkact.source
        self.target = atkact.target
        self.fatetell_target = atkact.source

    def fatetell_action(self, ft):
        act = self.atkact
        if ft.succeeded:
            act.__class__ = classmix(InevitableAttack, act.__class__)
        else:
            mark(act, 'freaking_power')

        return True

    @staticmethod
    def fatetell_cond(c):
        return c.color == Card.RED


class FreakingPowerHandler(EventHandler):
    interested = ('action_after', 'action_before', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack) and not marked(act, 'freaking_power'):
            src = act.source
            if not src.has_skill(FreakingPower): return act
            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act
            tgt = act.target
            Game.getgame().process_action(FreakingPowerAction(act))

        elif evt_type == 'action_after' and isinstance(act, Damage):
            g = Game.getgame()

            pact = g.action_stack[-1]
            if not marked(pact, 'freaking_power'):
                return act

            src, tgt = pact.source, act.target
            if tgt.dead: return act

            catnames = ('cards', 'showncards', 'equips')
            card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
            if card:
                g.players.exclude(tgt).reveal(card)
                g.process_action(DropCards(src, tgt, [card]))

        return act


@register_character_to('common', '-kof')
class Yugi(Character):
    skills = [Assault, FreakingPower]
    eventhandlers_required = [FreakingPowerHandler]
    maxlife = 4


@register_character_to('kof')
class YugiKOF(Character):
    skills = [AssaultKOF, FreakingPower]
    eventhandlers_required = [AssaultKOFHandler, FreakingPowerHandler]
    maxlife = 4
