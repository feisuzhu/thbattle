from .baseclasses import *
from ..actions import *
from ..cards import *

class Problem(Skill):
    associated_action = None
    target = t_None
    

class ProblemDamageAction(UserAction):
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


class ProblemHealAction(DrawCards):
    pass

class ProblemHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_after': return act

        if isinstance(act, Damage) or isinstance(act, Heal):
            tgt = act.target
            if tgt.dead: return act
            if not tgt.has_skill(Problem): return act
            src = act.source
            if not src: return act
            if not user_choose_option(self, tgt): return act

            g = Game.getgame()
            if isinstance(act, Damage):
                g.process_action(ProblemDamageAction(tgt, src))
            else:  # Heal
                g.process_action(ProblemHealAction(src, 1))
                
        return act


class EndlessNight(TreatAsSkill):
    treat_as = SealingArrayCard
    def check(self):
        return False  # can only launch by handler


class EndlessNightHandler(EventHandler):
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

        for a in reversed(g.action_stack):
            if isinstance(a, ActionStage):
                turn_player = a.target
                break
        else:
            assert False, 'Should not happen'

        tgt = act.target
        
        for p in g.players.exclude(turn_player):
            if p.dead or p is tgt: continue
            if not p.has_skill(EndlessNight): continue
            
            if not user_choose_option(self, p): continue

            cats = [p.cards, p.showncards, p.equips]
            cards = user_choose_cards(self, p, cats)

            if cards:
                g.players.exclude(p).reveal(cards)
                card = EndlessNight.wrap(cards, p)
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
    skills = [Problem, EndlessNight]
    eventhandlers_required = [ProblemHandler, EndlessNightHandler]
    maxlife = 3
