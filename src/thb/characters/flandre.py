# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from thb.actions import Damage, DrawCards, LaunchCard, PlayerDeath, PlayerTurn
from thb.cards import AttackCard, DuelCard, Heal, Skill, UserAction, t_None
from thb.characters.baseclasses import Character, register_character_to


# -- code --
class ForbiddenFruits(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class ForbiddenFruitsHeal(Heal):
    pass


class ForbiddenFruitsHandler(EventHandler):
    interested = ('action_after',)
    execute_after = ('DyingHandler',)
    execute_before = (
        'AyaRoundfanHandler',
        'NenshaPhoneHandler',
        'DilemmaHandler',
        'DecayDamageHandler',
        'EchoHandler',
        'MelancholyHandler',
        'MajestyHandler',
        'MasochistHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if act.cancelled: return act
            if not src: return act
            if not src.has_skill(ForbiddenFruits): return act

            g = Game.getgame()
            for lc in reversed(g.action_stack):
                if isinstance(lc, LaunchCard):
                    break
            else:
                return act

            c = lc.card
            if not (c.is_card(AttackCard) or c.is_card(DuelCard)):
                return act

            if lc.source is src:
                n = act.amount * 2 - (src.maxlife - src.life)
                if n > 0:
                    g.process_action(DrawCards(src, n))
                    src.maxlife - src.life and g.process_action(ForbiddenFruitsHeal(src, src, src.maxlife - src.life))
                else:
                    g.process_action(ForbiddenFruitsHeal(src, src, act.amount * 2))

        return act


# @register_character_to('common')
class Flandre(Character):
    skills = [ForbiddenFruits]
    eventhandlers_required = [ForbiddenFruitsHandler]
    maxlife = 3
