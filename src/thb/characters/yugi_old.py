# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, cast

# -- third party --
# -- own --
from thb.actions import Damage, DropCards, FatetellAction, LaunchCard, random_choose_card
from thb.cards.base import Card, Skill, VirtualCard
from thb.cards.classes import AttackCard, BaseAttack, InevitableAttack, RedUFOSkill, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler, THBAction
from utils.misc import classmix

# -- typing --
if TYPE_CHECKING:
    from thb.thbkof import THBattleKOF  # noqa: F401


# -- code --
class Assault(RedUFOSkill):
    skill_category = ['character', 'passive', 'compulsory']
    increment = 1


class AssaultKOF(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


class AssaultAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class AssaultKOFHandler(THBEventHandler):
    interested = ['character_debut']
    game: THBattleKOF

    def handle(self, evt_type, arg):
        if evt_type == 'character_debut':
            old, new = arg
            if not new.has_skill(AssaultKOF):
                return arg

            g = self.game
            op = g.get_opponent(new)
            lc = LaunchCard(new, [op], AssaultAttack(new))
            if not lc.can_fire():
                return arg

            if g.user_input([new], ChooseOptionInputlet(self, (False, True))):
                g.process_action(lc)

        return arg


class FreakingPower(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


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
            act._['freaking_power'] = True

        return True

    @staticmethod
    def fatetell_cond(c):
        return c.color == Card.RED


class FreakingPowerHandler(THBEventHandler):
    interested = ['action_after', 'action_before']
    execute_before = ['AyaRoundfanHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack) and not act._['freaking_power']:
            src = act.source
            g = self.game
            if not src.has_skill(FreakingPower): return act
            if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act
            tgt = act.target
            g.process_action(FreakingPowerAction(act))

        elif evt_type == 'action_after' and isinstance(act, Damage):
            g = self.game

            if act.cancelled: return act

            pact = cast(THBAction, g.action_stack[-1])
            if not pact._['freaking_power']:
                return act

            src, tgt = pact.source, act.target
            if tgt.dead: return act

            if not (tgt.cards or tgt.showncards or tgt.equips):
                return act

            catnames = ('cards', 'showncards', 'equips')
            card = g.user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
            card = card or random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
            if card:
                g.players.exclude(tgt).reveal(card)
                g.process_action(DropCards(src, tgt, [card]))

        return act


@register_character_to('common', '-kof')
class Yugi(Character):
    skills = [Assault, FreakingPower]
    eventhandlers = [FreakingPowerHandler]
    maxlife = 4


@register_character_to('kof')
class YugiKOF(Character):
    skills = [AssaultKOF, FreakingPower]
    eventhandlers = [AssaultKOFHandler, FreakingPowerHandler]
    maxlife = 4
