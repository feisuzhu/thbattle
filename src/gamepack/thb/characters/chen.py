# -*- coding: utf-8 -*-
from game.autoenv import EventHandler
from .baseclasses import Character, register_character
from ..actions import ForEach, LaunchCard
from ..cards import Skill, AttackCard, DollControlCard, RejectCard, InstantSpellCardAction


class FlyingSkandaAction(ForEach):
    @property
    def action_cls(self):
        skill = self.associated_card
        card = skill.associated_cards[0]
        action = card.associated_action
        return action

    def is_valid(self):
        p = self.source
        if p.tags['turn_count'] <= p.tags['flying_skanda']:
            return False
        if any(t.dead for t in self.target_list):
            return False
        return True


class FlyingSkanda(Skill):
    associated_action = FlyingSkandaAction

    def target(self, g, source, tl):
        cl = self.associated_cards
        if not cl: return ([], False)
        c = cl[0]
        if len(tl) < 2:
            return c.target(g, source, tl)
        else:
            rst = c.target(g, source, tl[:-1])
            a = tl[-1]
            if a is source:
                return rst[0], False
            else:
                return rst[0] + [a], rst[1]

    @property
    def distance(self):
        cl = self.associated_cards
        if not cl: return 0
        return cl[0].distance

    def check(self):
        cl = self.associated_cards
        if len(cl) != 1: return False
        c = cl[0]
        if c.is_card(AttackCard): return True

        if c.is_card(DollControlCard): return False
        if c.is_card(RejectCard): return False

        act = c.associated_action
        if not issubclass(act, InstantSpellCardAction): return False
        return True

    def is_card(self, cls):
        cl = self.associated_cards
        if cl and cl[0].is_card(cls): return True
        return isinstance(self, cls)


class FlyingSkandaHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, LaunchCard):
            if not act.card.is_card(FlyingSkanda): return act
            act.source.tags['flying_skanda'] = act.source.tags['turn_count']
        return act


@register_character
class Chen(Character):
    skills = [FlyingSkanda]
    eventhandlers_required = [FlyingSkandaHandler]
    maxlife = 4
