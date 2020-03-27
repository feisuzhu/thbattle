# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game, user_input
from game.base import EventHandler
from thb.actions import DrawCards, DropCardStage, DummyAction, FinalizeStage, GenericAction
from thb.actions import LifeLost, MaxLifeChange, Pindian, PlayerDeath, PlayerTurn, TryRevive
from thb.actions import UserAction, ttags
from thb.cards import Heal, Skill, t_None, t_OtherOne
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class GuidedDeathLifeLost(LifeLost):
    pass


class GuidedDeathEffect(GenericAction):
    def __init__(self, source, target_list):
        self.source = source
        self.target = source
        self.target_list = target_list

    def apply_action(self):
        g = Game.getgame()

        for p in self.target_list:
            g.process_action(GuidedDeathLifeLost(p, p))

        return True


class GuidedDeathAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        if tgt.dead: return True
        g = Game.getgame()
        ttags(src)['guided_death_active_use'] = tgt
        g.process_action(GuidedDeathLifeLost(src, tgt, 1))
        return True


class GuidedDeath(Skill):
    associated_action = GuidedDeathAction
    skill_category = ('character', 'active')
    target = t_OtherOne
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return len(cl) == 0


class GuidedDeathHandler(EventHandler):
    interested = ('action_apply',)
    execute_before = ('SoulDrainHandler',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            g = Game.getgame()

            src = act.target
            if not src.has_skill(GuidedDeath) or src.dead:
                return act

            p = ttags(src)['guided_death_active_use']
            if p:
                g.process_action(Heal(p, p, 1))
            else:
                tl = [p for p in g.players.rotate_to(src) if p.life == 1 and p is not src]
                if not tl:
                    return act

                g.process_action(GuidedDeathEffect(src, tl))

        return act


class SoulDrain(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SoulDrainEffect(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        assert tgt.life <= 0

        g.process_action(DrawCards(src, 1))

        if not tgt.cards and not tgt.showncards:
            return True

        if src is tgt:
            return True

        if user_input([src], ChooseOptionInputlet(self, (False, True))):
            if g.process_action(Pindian(src, tgt)):
                g.process_action(MaxLifeChange(src, tgt, -tgt.maxlife + 1))
            else:
                g.process_action(Heal(src, tgt, -tgt.life + 1))

        return True


class SoulDrainHandler(EventHandler):
    interested = ('action_before',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, TryRevive):
            g = Game.getgame()
            tgt = act.target

            for p in g.players:
                if p.has_skill(SoulDrain) and not p.dead and p is not tgt:
                    break
            else:
                return act

            for a in reversed(g.action_stack):
                if isinstance(a, PlayerTurn):
                    if a.target is not p:
                        return act
                    else:
                        break
            else:
                return act

            g.process_action(SoulDrainEffect(p, tgt))

            if tgt.life > 0:
                # Abort TryRevive process
                return DummyAction(p, act.target)
            else:
                return act

        return act


class PerfectCherryBlossomHandler(EventHandler):
    interested = ('action_apply', 'action_before')
    execute_after = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()

            for p in g.players:
                if p.has_skill(PerfectCherryBlossom) and not p.dead and p is not act.target:
                    break
            else:
                return act

            g.process_action(PerfectCherryBlossomExtractAction(p, act.target))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(PerfectCherryBlossom):
                return act

            act.dropn -= tgt.maxlife - tgt.life

        return act


class PerfectCherryBlossomExtractAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        if src.life >= src.maxlife:
            choice = 'maxlife'
        elif user_input([src], ChooseOptionInputlet(self, ('life', 'maxlife'))) == 'maxlife':
            choice = 'maxlife'
        else:
            choice = 'life'

        if choice == 'life':
            g.process_action(Heal(src, src, 1))
        else:
            g.process_action(MaxLifeChange(src, src, 1))

        return True


class PerfectCherryBlossom(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


@register_character_to('common', '-kof')
class Yuyuko(Character):
    skills = [GuidedDeath, SoulDrain, PerfectCherryBlossom]
    eventhandlers_required = [GuidedDeathHandler, SoulDrainHandler, PerfectCherryBlossomHandler]
    maxlife = 3
