# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import cast

# -- third party --
# -- own --
# -- errord --
from thb.actions import DrawCards, MigrateCardsTransaction, UserAction
from thb.cards.base import Skill
from thb.cards.classes import Heal, t_None, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler


# -- code --
class Psychopath(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None()


class NetoruAction(UserAction):
    def apply_action(self):
        g = self.game
        src = self.source
        src.tags['netoru_tag'] = src.tags['turn_count']
        tgt = self.target
        g.process_action(Heal(src, tgt))
        if src.life < src.maxlife:
            g.process_action(Heal(src, src))
        return True

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.tags['netoru_tag'] >= src.tags['turn_count']:
            return False
        return not (tgt.dead or tgt.life >= tgt.maxlife)


class Netoru(Skill):
    associated_action = NetoruAction
    skill_category = ['character', 'active']
    target = t_OtherOne()
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return cl and len(cl) == 2 and all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards')
            for c in cl
        )


class PsychopathDrawCards(DrawCards):
    pass


class PsychopathHandler(THBEventHandler):
    interested = ['post_card_migration']

    def handle(self, evt_type, arg):
        if evt_type == 'post_card_migration':
            g = self.game
            trans = cast(MigrateCardsTransaction, arg)
            for m in trans.movements:
                if m.fr.type != 'equips': continue
                src = m.fr.owner
                assert src
                if src.dead: continue
                if not src.has_skill(Psychopath): continue
                g.process_action(PsychopathDrawCards(src, 2))

        return arg


@register_character_to('common', '-kof')
class Rinnosuke(Character):
    skills = [Netoru, Psychopath]
    eventhandlers = [PsychopathHandler]
    maxlife = 3
