# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import Damage, DrawCards, LaunchCard, LifeLost, UserAction, migrate_cards
from thb.actions import skill_check, skill_wrap, user_choose_cards
from thb.cards.base import Card, Skill, VirtualCard, t_None
from thb.cards.classes import Heal, SealingArrayCard, TreatAs
from thb.cards.definition import BasicCard
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class Dilemma(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class DilemmaDamageAction(UserAction):
    card_usage = 'handover'

    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        g = self.game
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
        if card.is_card(Skill):
            return False

        if card.resides_in.type not in (
            'cards', 'showncards', 'equips'
        ): return False

        return card.suit == Card.DIAMOND


class DilemmaHealAction(DrawCards):
    def __init__(self, source, target, amount=2):
        self.source = source
        self.target = target
        self.amount = amount


class DilemmaHandler(THBEventHandler):
    interested = ['action_after']
    execute_after = ['DyingHandler']

    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, (Damage, Heal)): return act

        src = act.source
        tgt = act.target
        if tgt.dead: return act
        if not tgt.has_skill(Dilemma): return act
        if not src: return act

        self.dilemma_type = 'negative' if isinstance(act, Damage) else 'positive'
        g = self.game
        if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        if isinstance(act, Damage):
            g.process_action(DilemmaDamageAction(tgt, src))
        else:  # Heal
            g.process_action(DilemmaHealAction(tgt, src, 1))

        return act


class ImperishableNight(TreatAs, Skill):
    treat_as = SealingArrayCard
    skill_category = ['character', 'passive']

    def check(self):
        return self.game.current_player is not self.player


class ImperishableNightHandler(THBEventHandler):
    interested = ['action_after']
    card_usage = 'launch'

    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, LaunchCard): return act

        g = self.game

        card = act.card
        if not card: return act
        if not isinstance(card, BasicCard): return act
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
            if p is g.current_player: continue

            if not g.user_input([p], ChooseOptionInputlet(self, (False, True))):
                continue

            cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))

            if cards:
                g.players.reveal(cards)
                skill = skill_wrap(p, [ImperishableNight], cards, {})
                assert skill_check(skill)  # should not fail
                g.deck.register_vcard(skill)
                rst = g.process_action(LaunchCard(p, [tgt], skill))
                assert rst

        return act

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if card.resides_in.type not in (
            'cards', 'showncards', 'equips'
        ): return False
        if 'skill' in card.category: return False
        if card.color != Card.RED: return False
        return bool(set(card.category) & {'basic', 'equipment'})

    def ask_for_action_verify(self, p, cl, tl):
        tgt = self.target
        skill = skill_wrap(p, [ImperishableNight], cl, {})
        return LaunchCard(p, [tgt], skill).can_fire()


@register_character_to('common')
class Kaguya(Character):
    skills = [Dilemma, ImperishableNight]
    eventhandlers = [DilemmaHandler, ImperishableNightHandler]
    maxlife = 3
