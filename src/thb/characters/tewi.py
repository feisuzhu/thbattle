# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import cast

# -- third party --
# -- own --
# -- errord --
from thb.actions import DrawCards, MigrateCardsTransaction
from thb.cards.base import Skill
from thb.cards.classes import t_None
from thb.characters.base import Character, register_character_to
from thb.mode import THBEventHandler


# -- code --
class Luck(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None()


class LuckDrawCards(DrawCards):
    pass


class LuckHandler(THBEventHandler):
    interested = ['post_card_migration']

    def handle(self, evt_type, arg):
        if evt_type != 'post_card_migration':
            return arg

        trans = cast(MigrateCardsTransaction, arg)

        candidates = {}

        for m in trans.movements:
            p = m.fr.owner
            if not (p and p.has_skill(Luck)): continue
            if m.fr not in (p.cards, p.showncards): continue
            if p.cards or p.showncards: continue
            if p.dead: continue
            candidates[p] = 1

        for p in candidates:
            self.game.process_action(LuckDrawCards(p, 2))

        return arg


@register_character_to('common', '-kof')
class Tewi(Character):
    skills = [Luck]
    eventhandlers = [LuckHandler]
    maxlife = 4
