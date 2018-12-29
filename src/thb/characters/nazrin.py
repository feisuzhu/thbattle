# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import FatetellAction, FatetellStage, migrate_cards
from thb.cards.base import Card, Skill
from thb.cards.classes import GrazeCard, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class TreasureHuntAction(FatetellAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

    def fatetell_action(self, ft):
        if ft.succeeded:
            self.card = c = ft.card
            migrate_cards([c], self.target.cards, is_bh=True)
            return True

        return False

    def fatetell_cond(self, c):
        return c.color == Card.BLACK


class TreasureHunt(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class TreasureHuntHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['CiguateraHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            tgt = act.target
            if not tgt.has_skill(TreasureHunt): return act
            g = self.game
            while True:
                if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                    return act
                if not g.process_action(TreasureHuntAction(tgt, tgt)):
                    return act
        return act


class Agile(TreatAs, Skill):
    skill_category = ['character', 'active']
    treat_as = GrazeCard

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].suit in (Card.SPADE, Card.CLUB) and
            cl[0].resides_in.type in ('cards', 'showncards')
        )


class AgileKOF(TreatAs, Skill):
    skill_category = ['character', 'active']
    treat_as = GrazeCard

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].suit == Card.SPADE and
            cl[0].resides_in.type in ('cards', 'showncards')
        )


@register_character_to('common', '-kof')
class Nazrin(Character):
    skills = [TreasureHunt, Agile]
    eventhandlers = [TreasureHuntHandler]
    maxlife = 3


@register_character_to('kof')
class NazrinKOF(Character):
    skills = [TreasureHunt, AgileKOF]
    eventhandlers = [TreasureHuntHandler]
    maxlife = 3
