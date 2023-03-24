# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, cast

# -- third party --
# -- own --
from thb.actions import PrepareStage,Damage, DropCards, FatetellAction, LaunchCard, random_choose_card, UserAction, migrate_cards,ttags,ActionStage,PlayerTurn
from thb.cards.base import Card, Skill, VirtualCard
from thb.cards.classes import AttackCard, BaseAttack, InevitableAttack, TreatAs, t_None
from thb.cards.equipment import RepentanceStick
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler, THBAction
from utils.misc import classmix

# -- typing --
if TYPE_CHECKING:
    from thb.thbkof import THBattleKOF  # noqa: F401


# -- code --
class Assault(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None()


class AssaultHandler(THBEventHandler):
    interested = ['post_calcdistance']

    def handle(self, evt_type, arg):
        if evt_type == 'post_calcdistance':
            src, card, dist = arg
            if not src.has_skill(Assault):
                return arg

            cc = len(src.cards)+len(src.showncards)
            for t in dist:
                dist[t] = max(0, dist[t]-cc)

        return arg


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


class SplashProof(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


class SplashProofRetrieveAction(UserAction):
    def __init__(self, source: Character, target: Character, card: Card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        c = self.card
        if not c:
            return False

        tar = self.target

        ttags(tar)['splash_proof'] = True

        g = self.game
        shadow = SplashProof(tar)
        for a in g.action_stack:
            if isinstance(a, LaunchCard) and a.card is c:
                a.card = shadow
            elif getattr(a, 'associated_card', None) is c:
                a.associated_card = shadow

        migrate_cards([c], tar.cards,unwrap=True)

        return True
    
    def is_valid(self):
        return not ttags(self.target)['splash_proof'] and self.card


class SplashProofHandler(THBEventHandler):
    interested = ['action_before','action_after']
    execute_after=['RepentanceStickHandler']

    def handle(self, evt_type, act):
        g = self.game

        if evt_type=='action_after'and isinstance(act,BaseAttack):
            if act.succeeded: return act

            card=act.associated_card
            if not card: return act


        elif evt_type=='action_before' and isinstance(act,Damage):
            if not act.cancelled: return act

            pact = g.action_stack[-1]
            if not isinstance(pact,BaseAttack): return act
            card = getattr(pact, 'associated_card', None)
            if not card: return act

        else:
            return act
        
        src = act.source
        
        #if not src.has_skill(SplashProof):
        if not src.has_skill(Assault):
            return act
        
        try:
            current = PlayerTurn.get_current(g).target
        except IndexError:
            return act

        if current is not src:
            return act
        
        if ttags(src)['splash_proof']:
            return act
        
        if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
            return act
        
        g.process_action(SplashProofRetrieveAction(src, src, card))
            
        return act


@register_character_to('common', '-kof')
class Yugi(Character):
    skills = [Assault, FreakingPower]
    eventhandlers = [AssaultHandler, FreakingPowerHandler, SplashProofHandler]
    maxlife = 4


@register_character_to('kof')
class YugiKOF(Character):
    skills = [AssaultKOF, FreakingPower]
    eventhandlers = [AssaultKOFHandler, FreakingPowerHandler]
    maxlife = 4
