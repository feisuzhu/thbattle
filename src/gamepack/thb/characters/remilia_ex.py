# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character_to

from ..actions import UserAction, DropCards, LifeLost, LaunchCard, ForEach, DrawCards, ActionStage, DropCardStage, ask_for_action
from ..actions import random_choose_card, user_choose_cards
from ..cards import Card, Skill, InevitableAttack, AttackCard, DelayedLaunchCard
from ..cards import t_OtherOne, t_None, t_All, VirtualCard
from ..inputlets import ChoosePeerCardInputlet

from ..thbraid import use_faith

from .remilia import SpearTheGungnir, SpearTheGungnirHandler
from .remilia import VampireKiss, VampireKissHandler


class HeartBreakAction(InevitableAttack):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.damage = 2

    def apply_action(self):
        use_faith(self.source, 4)
        return InevitableAttack.apply_action(self)


class HeartBreak(Skill):
    associated_action = HeartBreakAction
    skill_category = ('character', 'active')
    target = t_OtherOne

    color = property(lambda _: Card.RED).setter(lambda _, v: None)

    def is_card(self, cls):
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 4


class NeverNightAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        use_faith(src, 3)
        src.tags['nevernight_tag'] = src.tags['turn_count']

        for p in self.target_list:
            if not (p.cards or p.showncards or p.equips):
                if p.faiths:
                    g.process_action(DropCards(p, p.faiths))
            else:

                catnames = ('cards', 'showncards', 'equips')
                cats = [getattr(p, i) for i in catnames]
                c = user_input([src], ChoosePeerCardInputlet(self, p, catnames))
                c = c or random_choose_card(cats)

                g.players.reveal(c)

                g.process_action(DropCards(p, [c]))

        return True

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['nevernight_tag']


class NeverNight(Skill):
    associated_action = NeverNightAction
    skill_category = ('character', 'active')
    target = t_All

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 3


class ScarletFogEffect(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        g = Game.getgame()
        p = self.target

        _pl = g.attackers[:]
        _pl.remove(p)
        pl = []
        atkcard = AttackCard()
        for t in _pl:
            if LaunchCard(p, [t], atkcard).can_fire():
                pl.append(t)

        if not pl:
            g.process_action(LifeLost(p, p, 1))
            return True

        _, rst = ask_for_action(self, (p, ), ('cards', 'showncards'), pl)
        if rst:
            c = rst[0][0]; t = rst[1][0]
            g.process_action(LaunchCard(p, [t], c))
        else:
            g.process_action(LifeLost(p, p, 1))

        return True

    def cond(self, cl):
        return len(cl) == 1 and cl[0].is_card(AttackCard)

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class ScarletFogAction(ForEach):
    action_cls = ScarletFogEffect

    def prepare(self):
        src = self.source
        tags = src.tags
        tags['scarletfog_tag'] = tags['turn_count']

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['scarletfog_tag']


class ScarletFog(Skill):
    associated_action = ScarletFogAction
    skill_category = ('character', 'active')
    target = t_All
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        c = cl[0]
        if c.is_card(VirtualCard): return False
        if c.color != Card.RED: return False
        return True


class QueenOfMidnight(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class QueenOfMidnightHandler(EventHandler):
    execute_after = ('SealingArrayHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(QueenOfMidnight): return act
            if act.cancelled: return act
            g.process_action(DrawCards(act.target, 4))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(QueenOfMidnight):
                act.dropn = max(act.dropn - 3, 0)

        return act


class Septet(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class SeptetHandler(EventHandler):
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DelayedLaunchCard):
            src = act.source
            tgt = act.target
            if not tgt.has_skill(Septet): return act
            self.action = act
            cl = user_choose_cards(self, src, ['cards', 'showncards'])
            g = Game.getgame()
            if cl:
                g.process_action(DropCards(src, cl))
            else:
                g.process_action(DropCards(tgt, [act.associated_card]))

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        c = cl[0]
        if not c.color == self.action.associated_card.color: return False
        cat = c.category
        return 'skill' not in cat and 'spellcard' in cat


class RemiliaEx2(Character):
    maxlife = 6
    skills = [
        HeartBreak,
        NeverNight,
        VampireKiss,
        SpearTheGungnir,
        ScarletFog,
        QueenOfMidnight,
        Septet,
    ]

    eventhandlers_required = [
        SpearTheGungnirHandler,
        VampireKissHandler,
        QueenOfMidnightHandler,
        SeptetHandler,
    ]


@register_character_to('raid_ex')
class RemiliaEx(Character):
    maxlife = 6
    skills = [NeverNight, SpearTheGungnir, VampireKiss]
    eventhandlers_required = [VampireKissHandler, SpearTheGungnirHandler]

    stage2 = RemiliaEx2
