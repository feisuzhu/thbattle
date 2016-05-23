# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import itertools

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, sync_primitive, user_input
from thb.actions import ActionStage, Damage, FinalizeStage, GenericAction, LaunchCard, ShowCards
from thb.actions import UserAction, migrate_cards, user_choose_cards
from thb.cards import AttackCard, Card, CardList, DuelCard, GrazeCard, RedUFOSkill, Skill, TreatAs
from thb.cards import VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from utils.misc import check


# -- code --
class SentryHideAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        tgt = self.target
        cl = getattr(tgt, 'momiji_sentry_cl', None)
        if cl is None:
            cl = CardList(tgt, 'momiji_sentry_cl')
            tgt.momiji_sentry_cl = cl
            tgt.showncardlists.append(cl)

        migrate_cards(self.cards, cl)
        return True


class SentryReturningAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        cl = getattr(tgt, 'momiji_sentry_cl', None)
        cl and migrate_cards(cl, tgt.cards, unwrap=True)
        return True


class SentryHandler(EventHandler):
    interested = ('action_after', 'action_apply')
    card_usage = 'launch'

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            g = Game.getgame()
            src, tgt = act.source, act.target
            if not (src and src.has_skill(Sentry)): return act
            if tgt.dead: return act
            pact = g.action_stack[-1]
            pcard = getattr(pact, 'associated_card', None)
            if not pcard: return act

            if not pcard.is_card(AttackCard) and not (pcard.is_card(DuelCard) and pact.source is src):
                return act

            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            cl = list(tgt.cards) + list(tgt.showncards)
            g.process_action(ShowCards(tgt, cl, [src]))

            if g.SERVER_SIDE:
                l = [c.is_card(AttackCard) or 'spellcard' in c.category for c in cl]
            else:
                l = [False for c in cl]

            l = sync_primitive(l, g.players)
            cl = list(itertools.compress(cl, l))
            g.process_action(SentryHideAction(src, tgt, cl))

        elif evt_type == 'action_apply' and isinstance(act, ActionStage):
            g = Game.getgame()
            for p in g.players:
                if p.dead: continue
                if not p.has_skill(Sentry): continue

                tgt = act.target
                if p is tgt: continue
                self.target = tgt  # for ui

                dist = LaunchCard.calc_distance(p, AttackCard())
                if dist.get(tgt, 1) > 0: continue
                cl = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
                if not cl: continue
                c = SentryAttack.wrap(cl, tgt)
                g.process_action(LaunchCard(p, [tgt], c))

        elif evt_type == 'action_after' and isinstance(act, FinalizeStage):
            tgt = act.target
            g = Game.getgame()
            g.process_action(SentryReturningAction(tgt, tgt))

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        return cl[0].is_card(AttackCard)

    def ask_for_action_verify(self, p, cl, tl):
        if not cl:
            return False

        tgt = self.target
        return LaunchCard(p, [tgt], cl[0]).can_fire()


class SentryAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class Sentry(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SolidShieldAttack(TreatAs, Skill):
    skill_category = ('character', 'active', 'passive')
    treat_as = AttackCard

    def check(self):
        try:
            c, = self.associated_cards
            check(c.resides_in is not None)
            check(c.resides_in.type in ('cards', 'showncards', 'equips'))
            check(c.color == Card.BLACK)
            p = self.player
            check(len(p.cards) + len(p.showncards) > p.life)
            return True
        except Exception:
            return False


class SolidShieldGraze(TreatAs, Skill):
    skill_category = ('character', 'active', 'passive')
    treat_as = GrazeCard

    def check(self):
        try:
            c, = self.associated_cards
            check(c.resides_in is not None)
            check(c.resides_in.type in ('cards', 'showncards', 'equips'))
            check(c.color == Card.RED)
            p = self.player
            check(len(p.cards) + len(p.showncards) <= p.life)
            return True
        except Exception:
            return False


class SharpEye(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


class SharpEyeKOF(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


@register_character_to('common')
class Momiji(Character):
    skills = [Sentry, SolidShieldAttack, SolidShieldGraze]
    eventhandlers_required = [SentryHandler]
    maxlife = 4
