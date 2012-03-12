# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *

class FindAction(UserAction):
    def __init__(self, source, target):
        assert source == target
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        cards = self.associated_card.associated_cards
        n = len(cards)
        # card will be dropped at LaunchCard
        #g.process_action(DropCards(self.target, cards))
        g.process_action(DrawCards(self.target, n))
        return True

class Find(Skill):
    associated_action = FindAction
    target = 'self'
    def check(self):
        return len(self.associated_cards)

@register_character
class LittleDevil(Character):
    skills = [Find]
    eventhandlers_required = []
    maxlife = 4
