# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import ActionStageLaunchCard
from ..cards import Card, DummyCard, Skill, TreatAs
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler


# -- code --
class Morphing(TreatAs, Skill):
    skill_category = ('character', 'active')

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
        return Card.card_classes.get(params.get('mamizou_morphing'))


class MorphingHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, ActionStageLaunchCard):
            c = arg.card
            if c.is_card(Morphing):
                src = arg.source
                src.tags['mamizou_morphing_tag'] = src.tags['turn_count']

        elif evt_type == 'action_can_fire':
            act, valid = arg
            if isinstance(act, ActionStageLaunchCard):
                c = act.card
                if c.is_card(Morphing):
                    t = act.source.tags
                    if t['mamizou_morphing_tag'] >= t['turn_count']:
                        return act, False

        return arg


@register_character_to('common', '-kof')
class Mamizou(Character):
    skills = [Morphing]
    eventhandlers_required = [MorphingHandler]
    maxlife = 4
