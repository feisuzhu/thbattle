# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, LaunchCard, Damage, DrawCards, LaunchCardAction, LifeLost
from ..actions import user_choose_cards, migrate_cards, skill_transform, user_input_action
from ..cards import Skill, t_None, Card, SealingArrayCard, TreatAsSkill, VirtualCard, Heal
from ..inputlets import ChooseOptionInputlet


class Dilemma(Skill):
    associated_action = None
    target = t_None


class DilemmaDamageAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        g = Game.getgame()
        if cards:
            self.peer_action = 'card'
            g.players.exclude(tgt).reveal(cards)
            migrate_cards(cards, src.cards)
        else:
            self.peer_action = 'life'
            g.process_action(LifeLost(src, tgt, 1))

        return True

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if not card.resides_in.type in (
            'cards', 'showncards', 'equips'
        ): return False

        return card.suit == Card.DIAMOND


class DilemmaHealAction(DrawCards):
    def __init__(self, source, target, amount=2):
        self.source = source
        self.target = target
        self.amount = amount


class DilemmaHandler(EventHandler):
    execute_after = ('DyingHandler', )

    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, (Damage, Heal)): return act

        src = act.source
        tgt = act.target
        if tgt.dead: return act
        if not tgt.has_skill(Dilemma): return act
        if not src: return act

        self.dilemma_type = 'negative' if isinstance(act, Damage) else 'positive'
        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        g = Game.getgame()
        if isinstance(act, Damage):
            g.process_action(DilemmaDamageAction(tgt, src))
        else:  # Heal
            g.process_action(DilemmaHealAction(tgt, src, 1))

        return act


class ImperishableNight(TreatAsSkill):
    treat_as = SealingArrayCard

    def check(self):
        return Game.getgame().current_turn is not self.player


class ImperishableNightHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, LaunchCardAction): return act

        g = Game.getgame()

        card = act.card
        if not card: return act
        if 'basic' not in card.category: return act
        if card.color != Card.RED: return act

        if card.is_card(VirtualCard):
            rawcards = VirtualCard.unwrap([card])
        else:
            rawcards = [card]

        if not all(
            c.resides_in is None or c.resides_in.type == 'droppedcard'
            for c in rawcards
        ): return act

        tgt = act.source
        self.target = tgt  # for ui

        if tgt.dead: return act

        for p in g.players:
            if p.dead or p is tgt: continue
            if not p.has_skill(ImperishableNight): continue
            if p is g.current_turn: continue

            if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                continue

            def action(p, cl, pl):
                skill = skill_transform(p, [ImperishableNight], cl, {})
                return LaunchCard(p, [tgt], skill)
                
            action = user_input_action(self, action, [p], ('cards', 'showncards', 'equips'), [])

            if action:
                g.process_action(action)

        return act

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if not card.resides_in.type in (
            'cards', 'showncards', 'equips'
        ): return False
        if 'skill' in card.category: return False
        if card.color != Card.RED: return False
        return bool(set(card.category) & {'basic', 'equipment'})


@register_character
class Kaguya(Character):
    skills = [Dilemma, ImperishableNight]
    eventhandlers_required = [DilemmaHandler, ImperishableNightHandler]
    maxlife = 3
