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
            g.process_action(LifeLost(tgt, tgt, 1))

        return True

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if card.resides_in.type == 'fatetell':
            return False
        return card.suit == Card.DIAMOND


class DilemmaHealAction(DrawCards):
    pass

class DilemmaHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act

        if isinstance(act, (Damage, Heal)):
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Dilemma): return act
            src = act.source
            if not src: return act
            if not user_choose_option(self, tgt): return act

            g = Game.getgame()
            if isinstance(act, Damage):
                g.process_action(DilemmaDamageAction(tgt, src))
            else:  # Heal
                g.process_action(DilemmaHealAction(src, 1))
                
        return act


class ImperishableNight(TreatAsSkill):
    treat_as = SealingArrayCard
    def check(self):
        return False  # can only launch by handler


class ImperishableNightHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act
        if not isinstance(act, DropUsedCard): return act

        g = Game.getgame()

        pact = g.action_stack[-1]
        if not isinstance(pact, LaunchCardAction): return act

        cards = act.cards
        assert len(cards) == 1
        card = cards[0]
        if 'basic' not in card.category : return act 
        if card.suit != Card.DIAMOND: return act

        turn_player = g.current_turn
        tgt = act.target
        
        for p in g.players.exclude(turn_player):
            if p.dead or p is tgt: continue
            if not p.has_skill(ImperishableNight): continue
            
            if not user_choose_option(self, p): continue

            cats = [p.cards, p.showncards, p.equips]
            cards = user_choose_cards(self, p, cats)

            if cards:
                g.players.exclude(p).reveal(cards)
                card = ImperishableNight.wrap(cards, p)
                g.deck.register_vcard(card)
                card.move_to(p.cards)
                g.process_action(LaunchCard(p, [tgt], card))

        return act

    def cond(self, cards):
        if len(cards) != 1: return False
        card = cards[0]
        if card.resides_in.type == 'fatetell':
            return False
        return card.suit == Card.DIAMOND


@register_character
class Kaguya(Character):
    skills = [Dilemma, ImperishableNight]
    eventhandlers_required = [DilemmaHandler, ImperishableNightHandler]
    maxlife = 3
