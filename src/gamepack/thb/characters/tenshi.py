# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCards, Fatetell, GenericAction, LaunchCard, UserAction
from ..actions import ask_for_action, migrate_cards
from ..cards import Card, Skill, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class Masochist(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MasochistAction(UserAction):
    no_reveal = True
    card_usage = 'handover'

    def __init__(self, target, n):
        self.source, self.target, self.amount = target, target, n

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        a = DrawCards(tgt, self.amount * 2)
        g.process_action(a)
        self.cards = cards = a.cards
        n = len(cards)
        while n > 0:
            pl = [p for p in g.players if not p.dead]
            pl.remove(tgt)
            _, rst = ask_for_action(self, [tgt], ('cards',), pl)
            if not rst: return True
            cl, pl = rst
            pl[0].reveal(cl)
            migrate_cards(cl, pl[0].cards)
            n -= len(cl)

        return True

    def cond(self, cl):
        cards = self.cards
        return all(c in cards for c in cl)

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class MasochistHandler(EventHandler):
    interested = (
        ('action_after', Damage),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Masochist): return act
            if not act.amount: return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(MasochistAction(tgt, act.amount))

        return act


class ScarletPerception(Skill):
    distance = 1
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class ScarletPerceptionAction(GenericAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        migrate_cards([self.card], self.source.cards)
        return True


class ScarletPerceptionHandler(EventHandler):
    interested = (
        ('action_after', Fatetell),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            tgt = act.target
            if act.card.color != Card.RED: return act

            g = Game.getgame()
            pl = [p for p in g.players if p.has_skill(ScarletPerception) and not p.dead]
            assert len(pl) <= 1

            if pl:
                p = pl[0]
                dist = LaunchCard.calc_distance(p, ScarletPerception(p))
                if dist.get(tgt, 1) <= 0:
                    g.process_action(ScarletPerceptionAction(p, tgt, act.card))

        return act


@register_character
class Tenshi(Character):
    skills = [Masochist, ScarletPerception]
    eventhandlers_required = [MasochistHandler, ScarletPerceptionHandler]
    maxlife = 3
