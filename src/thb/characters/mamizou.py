# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionLimitExceeded, ActionStageLaunchCard
from thb.cards.base import DummyCard, PhysicalCard, Skill
from thb.cards.classes import TreatAs
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler


# -- code --
class Morphing(TreatAs, Skill):
    skill_category = ['character', 'active']

    @property
    def treat_as(self):
        return self.get_morph_cls() or DummyCard

    def check(self):
        cl = self.associated_cards

        if not all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards')
            for c in cl
        ): return False

        return self.is_morph_valid()

    def is_morph_valid(self):
        cls = self.get_morph_cls()
        if not cls or 'delayed_spellcard' in cls.category:
            return False

        cl = self.associated_cards
        cats = set(cl[0].category)
        cats.update(cl[1].category)

        if 'skill' in cats:
            return False

        if not cats & set(cls.category) & {'basic', 'spellcard'}:
            return False

        return True

    def get_morph_cls(self):
        params = getattr(self, 'action_params', {})
        return PhysicalCard.classes.get(params.get('mamizou_morphing'))

    @classmethod
    def list_morph_cards(cls, cl):
        if len(cl) != 2:
            return []

        cats = set(cl[0].category)
        cats.update(cl[1].category)
        if 'skill' in cats:
            return []

        cats &= {'basic', 'spellcard'}

        if not cats:
            return []

        if 'spellcard' in cats:
            cats.discard('spellcard')
            cats.add('instant_spellcard')

        rst = [c() for c in PhysicalCard.classes.values() if set(c.category) & cats]

        def rank(c):
            cat = (set(c.category) & cats).pop()
            if cat == 'basic':
                return 1
            elif cat == 'instant_spellcard':
                return 2
            else:
                return 100

        rst.sort(key=rank)
        return rst


class MorphingHandler(THBEventHandler):
    interested = ['action_after', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStageLaunchCard):
            c = act.card
            if c.is_card(Morphing):
                src = act.source
                src.tags['mamizou_morphing_tag'] = src.tags['turn_count']

        elif evt_type == 'action_shootdown':
            if isinstance(act, ActionStageLaunchCard):
                c = act.card
                if c.is_card(Morphing):
                    t = act.source.tags
                    if t['mamizou_morphing_tag'] >= t['turn_count']:
                        raise ActionLimitExceeded

        return act


@register_character_to('common', '-kof')
class Mamizou(Character):
    skills = [Morphing]
    eventhandlers = [MorphingHandler]
    maxlife = 4
