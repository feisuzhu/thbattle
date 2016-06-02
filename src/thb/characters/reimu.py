# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InterruptActionFlow, user_input
from thb.actions import ActionStage, Damage, DrawCards, FinalizeStage, LaunchCard, PlayerRevive
from thb.actions import UserAction, migrate_cards, ttags, user_choose_cards
from thb.cards import AttackCard, Card, GreenUFOSkill, RejectCard, Skill, TreatAs, UFOSkill, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class Flight(GreenUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')

    @staticmethod
    def increment(src):
        for c in src.equips:
            if issubclass(c.equipment_skill, UFOSkill):
                return 0

        return 1


class SpiritualAttack(TreatAs, Skill):
    skill_category = ('character', 'active')
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
    skill_category = ('character', 'passive')
    target = t_None


class TributeAction(UserAction):
    def apply_action(self):
        cl = self.associated_card.associated_cards
        tgt = self.target
        tgt.reveal(cl)
        migrate_cards([self.associated_card], tgt.cards, unwrap=True)
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
    skill_category = ('active',)
    no_drop = True
    no_reveal = True
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


class TributeHandler(EventHandler):
    interested = ('action_after', 'game_begin', 'switch_character')

    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            self.add()

        elif evt_type == 'switch_character':
            cond = any([
                isinstance(p, Character) and p.has_skill(TributeTarget)
                for p in Game.getgame().players
            ])

            self.add() if cond else self.remove()

        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            self.add()

        return arg

    def add(self):
        g = Game.getgame()
        for p in g.players:
            if not isinstance(p, Character): continue
            if p.has_skill(TributeTarget): continue
            if not p.has_skill(Tribute):
                p.skills.append(Tribute)

    def remove(self):
        g = Game.getgame()
        for p in g.players:
            if not isinstance(p, Character): continue
            try:
                p.skills.remove(Tribute)
            except ValueError:
                pass

# -----------------------------------------


class ReimuExterminate(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ReimuExterminateAction(UserAction):
    def set_card(self, c):
        self.card = c

    def apply_action(self):
        assert self.card
        src, tgt = self.source, self.target
        c = self.card
        g = Game.getgame()
        return g.process_action(LaunchCard(src, [tgt], c, bypass_check=True))

    def cond(self, cl):
        return len(cl) == 1 and cl[0].is_card(AttackCard)


class ReimuExterminateHandler(EventHandler):
    interested = ('action_apply', 'action_after')
    execute_after = ('DyingHandler', 'CheatingHandler')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            if not act.source: return act
            src, tgt = act.source, act.target
            g = Game.getgame()
            if src is not g.current_player: return act
            if src is tgt: return act
            ttags(src)['did_damage'] = True

        elif evt_type == 'action_after' and isinstance(act, Damage):
            if not act.source: return act
            src, tgt = act.source, act.target
            g = Game.getgame()
            if not tgt.has_skill(ReimuExterminate): return act
            if src.dead: return act
            self.fire(tgt, g.current_player)

        elif evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            tgt = act.target
            if not ttags(tgt)['did_damage']:
                return act

            if tgt.dead:
                return act

            g = Game.getgame()
            for actor in g.players.rotate_to(g.current_player):
                if tgt is actor:
                    continue

                if not actor.has_skill(ReimuExterminate):
                    continue

                self.fire(actor, tgt)

        return act

    def fire(self, src, tgt):
        g = Game.getgame()
        act = ReimuExterminateAction(src, tgt)
        cl = user_choose_cards(act, src, ('cards', 'showncards'))
        if not cl:
            return

        assert len(cl) == 1
        act.set_card(cl[0])
        g.process_action(act)


class ReimuClear(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ReimuClearAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(DrawCards(src, 1))
        g.process_action(DrawCards(tgt, 1))
        if g.current_player is src:
            return True
        else:
            for act in reversed(g.action_stack):
                if isinstance(act, ActionStage):
                    raise InterruptActionFlow(unwind_to=act)
            else:
                return True


class ReimuClearHandler(EventHandler):
    interested = ('action_after',)
    execute_before = (
        'MasochistHandler',
        'DecayDamageHandler',
        'MelancholyHandler',
    )

    execute_after = (
        'IbukiGourdHandler',
        'AyaRoundfanHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not src: return act
            if not src.has_skill(ReimuClear): return act
            if src is tgt: return act
            if src.dead or tgt.dead: return act

            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                g = Game.getgame()
                g.process_action(ReimuClearAction(src, tgt))

        return act


@register_character_to('common')
class Reimu(Character):
    # skills = [SealingArraySkill, Flight, TributeTarget]
    # skills = [SpiritualAttack, Flight]
    skills = [ReimuExterminate, ReimuClear]
    eventhandlers_required = [ReimuExterminateHandler, ReimuClearHandler]
    maxlife = 3
