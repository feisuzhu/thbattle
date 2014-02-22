# -*- coding: utf-8 -*-
from .baseclasses import Character, register_character_to
from ..cards import Card, Heal, HealCard, Skill, t_None, t_One


class FirstAid(Skill):
    associated_action = None
    target = t_None

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1: return False
        c = cl[0]
        return bool(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards', 'equips') and
            c.suit in (Card.HEART, Card.DIAMOND)
        )

    def is_card(self, cls):
        if issubclass(HealCard, cls): return True
        return isinstance(self, cls)


class EirinHeal(Heal):
    def apply_action(self):
        src = self.source
        src.tags['medic_tag'] = src.tags['turn_count']
        return Heal.apply_action(self)

    def is_valid(self):
        src = self.source
        if src.tags.get('turn_count', 0) <= src.tags.get('medic_tag', 0):
            return False
        return True


class Medic(Skill):
    associated_action = EirinHeal
    target = t_One
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if bool(
            cl and len(cl) == 1 and
            cl[0].resides_in is not None and
            cl[0].resides_in.type in ('cards', 'showncards')
        ): return True
        return False


@register_character_to('common', '-kof')
class Eirin(Character):
    skills = [Medic, FirstAid]
    eventhandlers_required = []
    maxlife = 3
