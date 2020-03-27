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
        'ThirdEyeHandler',
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


class Exterminate(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class ExterminateAction(UserAction):

    def apply_action(self):
        tgt = self.target
        tgt.tags['exterminate'] = True
        for s in tgt.skills:
            if 'character' in s.skill_category:
                tgt.disable_skill(s, 'exterminate')

        return True


class ExterminateHandler(EventHandler):
    interested = ('choose_target',)

    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            act, tl = arg
            src = act.source
            g = Game.getgame()

            if not src.has_skill(Exterminate):
                return arg

            c = act.card
            if not c.is_card(AttackCard) and not c.is_card(DuelCard):
                return arg

            for tgt in tl:
                g.process_action(ExterminateAction(src, tgt))

        return arg


class ExterminateFadeHandler(EventHandler):
    interested = ('action_after', 'action_apply')

    def handle(self, evt_type, arg):
        if ((evt_type == 'action_after' and isinstance(arg, PlayerTurn)) or
            (evt_type == 'action_apply' and isinstance(arg, PlayerDeath) and arg.target.has_skill(Exterminate))):  # noqa

            g = Game.getgame()
            for p in g.players:
                if p.tags.pop('exterminate', ''):
                    p.reenable_skill('exterminate')

        return arg


@register_character_to('common')
class Flandre(Character):
    skills = [Exterminate, ForbiddenFruits]
    eventhandlers_required = [ExterminateHandler, ExterminateFadeHandler, ForbiddenFruitsHandler]
    maxlife = 3
