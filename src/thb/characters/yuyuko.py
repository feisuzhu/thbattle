# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import DrawCards, DummyAction, FinalizeStage, GenericAction, LifeLost
from thb.actions import MaxLifeChange, Pindian, TryRevive, UserAction, ttags
from thb.cards import Heal, Skill, t_None, t_OtherOne
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class GuidedDeath(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class GuidedDeathLifeLost(LifeLost):
    pass


class GuidedDeathEffect(GenericAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source

        for p in g.players.rotate_to(src):
            if p is src: continue
            if p.dead: continue
            if p.life > 1: continue
            g.process_action(GuidedDeathLifeLost(p, p))

        return True


class GuidedDeathHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            g = Game.getgame()

            src = act.target
            if not (src.has_skill(GuidedDeath) and not src.dead):
                return act

            if all(p.life > 1 for p in g.players):
                return act

            g.process_action(GuidedDeathEffect(src, src))

        return act


# 离魂：当一名角色进入濒死状态时，你摸1张牌，然后你可以与该角色拼点。若你赢，则将该角色的体力上限改为1。若你没赢，则将其体力值改为1。
class SoulDrain(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SoulDrainEffect(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(DrawCards(src, 1))

        assert tgt.life <= 0

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
            for p in g.players:
                if p.has_skill(SoulDrain) and not p.dead:
                    break
            else:
                return act

            tgt = act.target
            g.process_action(SoulDrainEffect(p, tgt))
            if tgt.life > 0:
                # Abort TryRevive process
                return DummyAction(p, act.target)
            else:
                return act

        return act


# 反魂：出牌阶段限一次，你可以令一名已受伤角色失去一点体力，然后其回复一点体力。若在该过程中该角色死亡，改为你回复一点体力。
class PerfectCherryBlossomAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        if tgt.dead: return True
        g = Game.getgame()
        ttags(src)['perfect_cherry_blossom'] = True
        g.process_action(LifeLost(src, tgt, 1))
        if tgt.dead:
            if src.life < src.maxlife:
                g.process_action(Heal(src, src, 1))
        else:
            g.process_action(Heal(tgt, tgt, 1))

        return True

    def is_valid(self):
        src, tgt = self.source, self.target
        if ttags(src)['perfect_cherry_blossom']:
            return False
        if not tgt.life < tgt.maxlife:
            return False
        return True


class PerfectCherryBlossom(Skill):
    associated_action = PerfectCherryBlossomAction
    skill_category = ('character', 'active')
    target = t_OtherOne

    def check(self):
        return not len(self.associated_cards)


@register_character_to('common')
class Yuyuko(Character):
    skills = [GuidedDeath, SoulDrain, PerfectCherryBlossom]
    eventhandlers_required = [GuidedDeathHandler, SoulDrainHandler]
    maxlife = 3
