# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --
# -- own --, PhysicalCard
from thb.actions import MaxLifeChange, PlayerRevive, UserAction
from thb.cards.base import Card, DummyCard, Skill, TreatAs, t_One, PhysicalCard
from thb.characters.base import Character
from thb.mode import THBEventHandler


# -- code --
log = logging.getLogger('THBattleDebug')


class DebugUseCard(TreatAs, Skill):
    skill_category = ['debug', 'active']

    @property
    def treat_as(self):
        return self.get_card_cls() or DummyCard

    def check(self):
        cl = self.associated_cards
        if self.treat_as is DummyCard:
            return False

        return all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards', 'equips')
            for c in cl
        )

    def get_card_cls(self):
        params = getattr(self, 'action_params', {})
        print(params)
        return PhysicalCard.classes.get(params.get('debug_card'))


class DebugDecMaxLife(Skill):
    skill_category = ['debug', 'active']

    class associated_action(MaxLifeChange, UserAction):
        def __init__(self, source, target):
            MaxLifeChange.__init__(self, source, target, -1)

    target = t_One

    def check(self):
        return not self.associated_cards


class DebugHandler(THBEventHandler):
    interested = ['action_after', 'game_begin', 'switch_character']
    '''
    Add this handler to game_eh to active debug skills
    '''

    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            self.add()

        elif evt_type == 'switch_character':
            self.add()

        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            self.add()

        return arg

    def add(self):
        g = self.game
        for p in g.players:
            if not isinstance(p, Character): continue
            if not p.has_skill(DebugUseCard):
                p.skills.extend([DebugUseCard, DebugDecMaxLife])
