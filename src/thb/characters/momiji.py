# -*- coding: utf-8 -*-

# -- stdlib --
import itertools

# -- third party --
# -- own --
from game.base import sync_primitive
from thb.actions import ActionStage, ActionStageLaunchCard, AskForCard, Damage, FinalizeStage
from thb.actions import GenericAction, LaunchCard, ShowCards, UserAction, migrate_cards, ttags
from thb.cards.base import CardList, Skill, VirtualCard
from thb.cards.classes import AttackCard, DollControlCard, DuelCard, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class DisarmHideAction(UserAction):
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


class DisarmReturningAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        cl = getattr(tgt, 'momiji_sentry_cl', None)
        cl and migrate_cards(cl, tgt.cards, unwrap=True)
        return True


class DisarmHandler(THBEventHandler):
    interested = ['action_after']
    execute_after = ['DeathHandler']

    card_usage = 'launch'

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            g = self.game
            src, tgt = act.source, act.target
            if not (src and src.has_skill(Disarm)): return act
            if tgt.dead: return act
            pact = g.action_stack[-1]
            pcard = getattr(pact, 'associated_card', None)
            if not pcard: return act

            if not pcard.is_card(AttackCard) and not (pcard.is_card(DuelCard) and pact.source is src):
                return act

            if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            cl = list(tgt.cards) + list(tgt.showncards)
            g.process_action(ShowCards(tgt, cl, [src]))

            if g.SERVER:
                l = [bool(c.is_card(AttackCard) or 'spellcard' in c.category) for c in cl]
            else:
                l = [False for c in cl]

            l = sync_primitive(l, g.players)
            cl = list(itertools.compress(cl, l))
            g.process_action(DisarmHideAction(src, tgt, cl))

        elif evt_type == 'action_after' and isinstance(act, FinalizeStage):
            tgt = act.target
            g = self.game
            g.process_action(DisarmReturningAction(tgt, tgt))

        return act


class Disarm(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class SentryAction(AskForCard):
    card_usage = 'launch'

    def __init__(self, source, target):
        AskForCard.__init__(self, source, source, AttackCard)
        self.victim = target

    def process_card(self, c):
        g = self.game
        src, tgt = self.source, self.victim
        c = SentryAttack.wrap([c], src)
        return g.process_action(LaunchCard(src, [tgt], c))


class SentryHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            g = self.game
            for p in g.players:
                if p.dead: continue
                if not p.has_skill(Sentry): continue

                tgt = act.target
                if p is tgt: continue
                self.target = tgt  # for ui

                dist = LaunchCard.calc_distance(p, AttackCard())
                if dist.get(tgt, 1) > 0: continue
                if not g.user_input([p], ChooseOptionInputlet(self, (False, True))):
                    continue

                g.process_action(SentryAction(p, tgt))

        return act


class SentryAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class Sentry(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class TelegnosisHandler(THBEventHandler):
    interested = ['calcdistance']
    execute_after = ['AttackCardHandler', 'UFODistanceHandler']

    processing = False

    def handle(self, evt_type, arg):
        if self.processing:
            return arg

        elif evt_type == 'calcdistance':
            src, c, dist = arg
            if not src.has_skill(Telegnosis): return arg
            if not c.is_card(AttackCard): return arg

            try:
                self.processing = True
                for p in dist:
                    if p is src: continue
                    d = LaunchCard.calc_distance(p, AttackCard())
                    if d[src] <= 0:
                        dist[p] = 0

            finally:
                self.processing = False

        return arg


class Telegnosis(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class SolidShieldHandler(THBEventHandler):
    interested = ['action_before']
    execute_after = ['AttackCardHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStageLaunchCard):
            src, tgt = act.source, act.target
            if not src or not tgt: return act
            ttags(src)['solid_shield_launch_count'] += 1
            if ttags(src)['solid_shield_launch_count'] != 1:
                return act

            if src is tgt: return act

            c = act.card
            if not (c.is_card(AttackCard) or 'instant_spellcard' in c.category):
                return act

            g = self.game
            for p in g.players.rotate_to(src):
                if p is src:
                    continue

                if p is tgt:
                    continue

                if not p.has_skill(SolidShield):
                    continue

                dist = LaunchCard.calc_distance(p, SolidShield(p))
                if dist[tgt] > 0:
                    continue

                cond = c.is_card(AttackCard) or 'instant_spellcard' in c.category
                cond = cond and (c.is_card(DollControlCard) or len(act.target_list) == 1)  # HACK HERE!
                if not cond:
                    return act

                if g.user_input([p], ChooseOptionInputlet(self, (False, True))):
                    g.process_action(SolidShieldAction(p, src, act))
                    break

        return act


class SolidShieldAction(UserAction):
    def __init__(self, source, target, action):
        self.source = source
        self.target = target
        self.action = action

    def apply_action(self):
        tgt = self.target
        lc = self.action
        assert isinstance(lc, ActionStageLaunchCard)

        cl = getattr(tgt, 'momiji_sentry_cl', None)
        if cl is None:
            cl = CardList(tgt, 'momiji_sentry_cl')
            tgt.momiji_sentry_cl = cl
            tgt.showncardlists.append(cl)

        migrate_cards([lc.card], cl, unwrap=True)
        lc.cancelled = True
        return True


class SolidShield(Skill):
    distance = 1
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


@register_character_to('common')
class Momiji(Character):
    # skills = [Disarm, Sentry, Telegnosis]
    skills = [Disarm, Sentry, SolidShield]
    # eventhandlers = [SentryHandler, DisarmHandler, TelegnosisHandler]
    eventhandlers = [SentryHandler, DisarmHandler, SolidShieldHandler]
    maxlife = 4
