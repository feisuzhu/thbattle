from .baseclasses import *
from ..actions import *
from ..cards import *


class Dilemma(Skill):
    associated_action = None
    target = t_None


class DilemmaDamageAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        cats = [tgt.cards, tgt.showncards, tgt.equips]
        cards = user_choose_cards(self, tgt, cats)
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
            'handcard', 'showncard', 'equips'
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
        if not user_choose_option(self, tgt): return act

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
        if not isinstance(act, DropUsedCard): return act

        g = Game.getgame()

        pact = g.action_stack[-1]
        if not isinstance(pact, LaunchCardAction): return act

        assert len(act.cards) == 1
        card = act.cards[0]
        if not card: return act
        if 'basic' not in card.category : return act
        if card.suit != Card.DIAMOND: return act

        tgt = pact.source
        assert act.target is tgt
        self.target = tgt  # for ui

        if tgt.dead: return act

        for p in g.players:
            if p.dead or p is tgt: continue
            if not p.has_skill(ImperishableNight): continue
            if p is g.current_turn: continue

            if not user_choose_option(self, p): continue

            cats = [p.cards, p.showncards, p.equips]
            cards = user_choose_cards(self, p, cats)

            if cards:
                skill = skill_wrap_by_class(p, [ImperishableNight], cards)
                assert skill  # should not fail
                rst = g.process_action(LaunchCard(p, [tgt], skill))
                assert rst

        return act

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if not card.resides_in.type in (
            'handcard', 'showncard', 'equips'
        ): return False
        return card.suit == Card.DIAMOND


@register_character
class Kaguya(Character):
    skills = [Dilemma, ImperishableNight]
    eventhandlers_required = [DilemmaHandler, ImperishableNightHandler]
    maxlife = 3
