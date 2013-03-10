# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

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
    target = t_OtherOne

    @property
    def color(self):
        return Card.RED
    
    @color.setter
    def color(self, val):
        pass

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

        for p in self.target_list:
            if not (p.cards or p.showncards or p.equips):
                if p.faiths:
                    g.process_action(DropCards(p, p.faiths))
            else:
                cats = [p.cards, p.showncards, p.equips]
                c = choose_peer_card(src, p, cats)
                if not c:
                    c = random_choose_card(cats)

                g.players.reveal(c)

                g.process_action(DropCards(p, [c]))

        return True


class NeverNight(Skill):
    associated_action = NeverNightAction
    target = t_All

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 3


class ScarletFogEffect(UserAction):
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

        rst = user_choose_cards_and_players(self, p, [p.cards, p.showncards], pl)
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
    target = t_All
    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        c = cl[0]
        if c.is_card(VirtualCard): return False
        if c.color != Card.RED: return False
        return True


class QueenOfMidnight(Skill):
    associated_action = None
    target = t_None


class QueenOfMidnightHandler(EventHandler):
    execute_before = ('FaithExchangeHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(QueenOfMidnight): return act
            g.process_action(DrawCards(act.target, 4))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(QueenOfMidnight):
                act.dropn = max(act.dropn - 3, 0)

        return act


class Septet(Skill):
    associated_action = None
    target = t_None


class SeptetHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DelayedLaunchCard):
            src = act.source
            tgt = act.target
            if not tgt.has_skill(Septet): return act
            self.action = act
            cl = user_choose_cards(self, src, [src.cards, src.showncards])
            g = Game.getgame()
            if cl:
                g.process_action(DropCards(src, cl))
            else:
                g.process_action(DropCards(tgt, [act.associated_card]))

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        if not cl[0].color == self.action.associated_card.color: return False
        if not issubclass(cl[0].associated_action, cards.SpellCardAction): return False
        return True


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


@register_ex_character
class RemiliaEx(Character):
    maxlife = 6
    skills = [NeverNight, SpearTheGungnir, VampireKiss]
    eventhandlers_required = [VampireKissHandler, SpearTheGungnirHandler]

    stage2 = RemiliaEx2
