# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import DropCards, GenericAction, MaxLifeChange, PlayerTurn, random_choose_card
from thb.cards.base import DummyCard, Skill, t_None
from thb.cards.classes import AttackCard, BaseAttack, GrazeCard, LaunchGraze, TreatAs
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class LoongPunch(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class Taichi(TreatAs, Skill):
    skill_category = ['character', 'active']

    @property
    def treat_as(self):
        cl = self.associated_cards
        if not cl: return DummyCard
        c = cl[0]
        if c.is_card(GrazeCard):
            return AttackCard
        if c.is_card(AttackCard):
            return GrazeCard
        return DummyCard

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1: return False
        c = cl[0]
        if not (c.is_card(AttackCard) or c.is_card(GrazeCard)): return False
        return c.resides_in is not None and c.resides_in.type in (
            'cards', 'showncards',
        )


class RiverBehind(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'awake']
    target = t_None


class LoongPunchAction(GenericAction):
    def __init__(self, source, target, _type):
        self.source = source
        self.target = target
        self.type = _type

    def apply_action(self):
        g = self.game
        src, tgt = self.source, self.target
        c = g.user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards')))
        c = c or random_choose_card(g, [tgt.cards, tgt.showncards])
        if not c: return False
        g.players.exclude(tgt).reveal(c)
        g.process_action(DropCards(src, tgt, [c]))
        return True


class LoongPunchHandler(THBEventHandler):
    interested = ['action_after']
    execute_after = ['DeathSickleHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, LaunchGraze):
            if not act.succeeded: return act
            g = self.game
            pact = g.action_stack[-1]
            if not isinstance(pact, BaseAttack): return act
            self.do_effect(pact.source, pact.target, 'attack')
            self.do_effect(pact.target, pact.source, 'graze')

        return act

    def do_effect(self, src, tgt, _type):
        if not src.has_skill(LoongPunch): return
        if not (tgt.cards or tgt.showncards): return
        g = self.game
        if not g.user_input([src], ChooseOptionInputlet(self, (False, True))): return

        g.process_action(LoongPunchAction(src, tgt, _type))


class RiverBehindAwake(GenericAction):
    def apply_action(self):
        tgt = self.target
        assert tgt.has_skill(RiverBehind)
        tgt.skills.remove(RiverBehind)
        tgt.skills.append(Taichi)
        g = self.game
        g.process_action(MaxLifeChange(tgt, tgt, -1))
        return True


class RiverBehindHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(RiverBehind): return act
            g = self.game
            if tgt.life <= 2 and tgt.life <= min(p.life for p in g.players if not p.dead):
                g.process_action(RiverBehindAwake(tgt, tgt))
        return act


@register_character_to('common')
class Meirin(Character):
    skills = [LoongPunch, RiverBehind]
    eventhandlers = [RiverBehindHandler, LoongPunchHandler]
    maxlife = 4
