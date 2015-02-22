# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb.actions import Damage, GenericAction, LaunchCard, LifeLost, MaxLifeChange, PlayerTurn
from gamepack.thb.actions import user_choose_players, ttags
from gamepack.thb.cards import Skill, t_None
from gamepack.thb.inputlets import ChooseOptionInputlet
from gamepack.thb.characters.baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class DestructionImpulse(Skill):
    distance = 1
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class DestructionImpulseAction(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        g.process_action(LifeLost(src, src))
        g.process_action(Damage(src, tgt))

        return True


class DestructionImpulseHandler(EventHandler):
    interested = ('action_after',)
    execute_before = ('CiguateraHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not src: return act
            if not src.has_skill(DestructionImpulse): return act

            g = Game.getgame()
            ttags(src)['destruction_tag'] = True

        elif evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(DestructionImpulse): return act

            g = Game.getgame()
            if ttags(tgt)['destruction_tag']: return act

            dist = LaunchCard.calc_distance(tgt, DestructionImpulse(tgt))
            dist.pop(tgt, '')

            for k in dist:
                dist[k] = max(dist[k], 0)

            nearest = min(dist.values())
            candidates = [p for p, d in dist.items() if d == nearest]
            candidates = [p for p in g.players if p in candidates]  # order matters

            if len(candidates) > 1:
                pl = user_choose_players(self, tgt, candidates)
                p = pl[0] if pl else candidates[0]
            else:
                p = candidates[0]

            g.process_action(DestructionImpulseAction(tgt, p))

        return act

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)

    def cond(self, cards):
        return not cards


class FourOfAKind(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class FourOfAKindAction(GenericAction):
    def __init__(self, source, target_act):
        self.source = source
        self.target_act = target_act
        self.target = target_act.target

    def apply_action(self):
        g = Game.getgame()
        src = self.source
        self.target_act.cancelled = True
        g.process_action(MaxLifeChange(src, src, -1))

        return True


class FourOfAKindHandler(EventHandler):
    interested = ('action_apply', 'action_before')
    execute_before = ('ProtectionHandler', )
    execute_after = (
        'RepentanceStickHandler',
        'DeathSickleHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled: return act

            tgt = act.target
            if not tgt.has_skill(FourOfAKind): return act
            if not act.amount <= tgt.life: return act

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g = Game.getgame()
                g.process_action(FourOfAKindAction(tgt, act))

        elif evt_type == 'action_apply' and isinstance(act, Damage):
            src = act.source

            if not src: return act
            if not src.has_skill(FourOfAKind): return act

            g = Game.getgame()

            for a in reversed(g.action_stack):
                if isinstance(a, LaunchCard):
                    break
            else:
                return act

            if src.life == 1:
                act.amount += 1

        return act


@register_character
class SpFlandre(Character):
    skills = [DestructionImpulse, FourOfAKind]
    eventhandlers_required = [DestructionImpulseHandler, FourOfAKindHandler]
    maxlife = 4
