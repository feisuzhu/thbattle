# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from game.base import InterruptActionFlow
from thb.actions import ActionStage, AskForCard, Damage, DrawCards, FinalizeStage, LaunchCard
from thb.actions import PlayerRevive, PlayerTurn, UserAction, migrate_cards, ttags
from thb.cards.base import Card, Skill
from thb.cards.classes import AttackCard, GreenUFOSkill, RejectCard, TreatAs, UFOSkill, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class Flight(GreenUFOSkill):
    skill_category = ['character', 'passive', 'compulsory']

    @staticmethod
    def increment(src):
        for c in src.equips:
            if issubclass(c.equipment_skill, UFOSkill):
                return 0

        return 1


class SpiritualAttack(TreatAs, Skill):
    skill_category = ['character', 'active']
    treat_as = RejectCard

    def check(self):
        cl = self.associated_cards
        if not(cl and len(cl) == 1 and cl[0].color == Card.RED):
            return False

        c = cl[0]
        if c.resides_in is None or c.resides_in.type not in (
            'cards', 'showncards'
        ): return False

        return True


class TributeTarget(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'boss']
    target = t_None


class TributeAction(UserAction):
    def apply_action(self):
        tgt = self.target
        migrate_cards([self.associated_card], tgt.showncards, unwrap=True)
        src = self.source
        src.tags['tribute_tag'] = src.tags['turn_count']
        return True

    def is_valid(self):
        p = self.source

        if p.tags.get('turn_count', 0) <= p.tags.get('tribute_tag', 0):
            return False

        tgt = self.target

        if tgt.dead: return False
        if len(tgt.cards) + len(tgt.showncards) >= tgt.maxlife: return False
        return True


class Tribute(Skill):
    associated_action = TributeAction
    skill_category = ['active']
    no_drop = True
    usage = 'handover'

    def check(self):
        cl = self.associated_cards
        rst = cl and len(cl) == 1 and (
            cl[0].resides_in is not None and
            cl[0].resides_in.type in ('cards', 'showncards')
        )
        return rst

    @staticmethod
    def target(g, source, tl):
        tl = [t for t in tl if not t.dead and t.has_skill(TributeTarget)]
        try:
            tl.remove(source)
        except ValueError:
            pass
        return (tl[-1:], bool(len(tl)))


class TributeHandler(THBEventHandler):
    interested = ['action_after', 'game_begin', 'switch_character']

    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            self.manage_tribute()

        elif evt_type == 'switch_character':
            self.manage_tribute()

        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            self.manage_tribute()

        return arg

    def manage_tribute(self):
        g = self.game
        cond = any([
            isinstance(p, Character) and p.has_skill(TributeTarget)
            for p in g.players
        ])

        if cond:
            for p in g.players:
                if not isinstance(p, Character): continue
                if p.has_skill(TributeTarget): continue
                if not p.has_skill(Tribute):
                    p.skills.append(Tribute)
        else:
            for p in g.players:
                if not isinstance(p, Character): continue
                try:
                    p.skills.remove(Tribute)
                except ValueError:
                    pass


# -----------------------------------------


class ReimuExterminate(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ReimuExterminateLaunchCard(LaunchCard):
    def __init__(self, source, target, card, cause):
        LaunchCard.__init__(self, source, [target], card, bypass_check=True)
        self.cause = cause  # for ui


class ReimuExterminateAction(AskForCard):
    card_usage = 'launch'

    def __init__(self, source, target, cause):
        AskForCard.__init__(self, source, source, AttackCard)
        self.victim = target
        self.cause = cause  # for ui

    def process_card(self, c):
        g = self.game
        return g.process_action(ReimuExterminateLaunchCard(self.source, self.victim, c, self.cause))


class ReimuExterminateHandler(THBEventHandler):
    interested = ['action_apply', 'action_after']
    execute_after = ['DyingHandler', 'CheatingHandler', 'IbukiGourdHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            if not act.source: return act
            src, tgt = act.source, act.target
            g = self.game
            current = PlayerTurn.get_current(g).target
            if src is not current: return act
            if src is tgt: return act
            ttags(src)['did_damage'] = True

        elif evt_type == 'action_after' and isinstance(act, Damage):
            if not act.source: return act
            src, tgt = act.source, act.target
            g = self.game
            cur = PlayerTurn.get_current(g).target
            if not cur: return act
            if not tgt.has_skill(ReimuExterminate): return act
            if cur.dead: return act
            if cur is tgt: return act
            g.process_action(ReimuExterminateAction(tgt, cur, 'damage'))

        elif evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            tgt = act.target
            if not ttags(tgt)['did_damage']:
                return act

            if tgt.dead:
                return act

            g = self.game
            current = PlayerTurn.get_current(g).target
            for actor in g.players.rotate_to(current):
                if tgt is actor:
                    continue

                if not actor.has_skill(ReimuExterminate):
                    continue

                g.process_action(ReimuExterminateAction(actor, tgt, 'finalize'))

        return act


class ReimuClear(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ReimuClearAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        g.process_action(DrawCards(src, 1))
        g.process_action(DrawCards(tgt, 1))
        current = PlayerTurn.get_current(g).target
        if current is src:
            return True
        else:
            for act in reversed(g.action_stack):
                if isinstance(act, ActionStage):
                    raise InterruptActionFlow(unwind_to=act)
            else:
                return True


class ReimuClearHandler(THBEventHandler):
    interested = ['action_after']
    execute_before = [
        'MasochistHandler',
        'DecayDamageHandler',
        'MelancholyHandler',
    ]

    execute_after = [
        'IbukiGourdHandler',
        'AyaRoundfanHandler',
        'MajestyHandler',
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not src: return act
            if not src.has_skill(ReimuClear): return act
            if src is tgt: return act
            if src.dead or tgt.dead: return act

            g = self.game
            if g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                g.process_action(ReimuClearAction(src, tgt))

        return act


@register_character_to('common', 'boss')
class Reimu(Character):
    # skills = [SealingArraySkill, Flight, TributeTarget]
    # skills = [SpiritualAttack, Flight]
    skills = [ReimuExterminate, ReimuClear]
    boss_skills = [TributeTarget]
    eventhandlers = [ReimuExterminateHandler, ReimuClearHandler, TributeHandler]
    maxlife = 4
