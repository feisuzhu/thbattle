# All generic and cards' Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, SyncPrimitive

from network import Endpoint
import random

from utils import check, check_type, CheckFailed

import logging
log = logging.getLogger('SimpleGame_Actions')

# ------------------------------------------
# aux functions
def user_choose_card(act, target, cond):
    from utils import check, CheckFailed
    g = Game.getgame()
    input = target.user_input('choose_card', act) # list of card ids

    try:
        check_type([[int, Ellipsis], [int, Ellipsis]], input)

        sid_list, cid_list = input

        cards = g.deck.getcards(cid_list)
        cs = set(cards)

        check(len(cs) == len(cid_list)) # repeated ids

        check(cs.issubset(set(target.cards))) # Whose cards?! Wrong ids?!

        if sid_list:
            cards = skill_wrap(target, sid_list, cards)

        g.players.exclude(target).reveal(cards)

        check(cond(cards))

        return cards
    except CheckFailed as e:
        print input
        import traceback
        traceback.print_exc(e)
        return None

def random_choose_card(target):
    c = random.choice(target.cards)
    v = SyncPrimitive(c.syncid)
    g = Game.getgame()
    g.players.reveal(v)
    v = v.value
    cl = [c for c in target.cards if c.syncid == v]
    assert len(cl) == 1
    return cl[0]

def skill_wrap(actor, sid_list, cards):
    g = Game.getgame()
    try:
        for skill_id in sid_list:
            check(isinstance(skill_id, int))
            check(0 <= skill_id < len(actor.skills))
            skill_action_cls = actor.skills[skill_id].associated_action
            check(skill_action_cls)
            skill = skill_action_cls(actor, cards)
            check(g.process_action(skill))
            cards = getattr(skill, 'cards', None)
            if not cards: return None
        from cards import CardWrapper
        check_type([CardWrapper], cards)
        card = cards[0]
        return card
    except CheckFailed as e:
        import traceback
        traceback.print_exc(e)
        return False

action_eventhandlers = set()
def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls

# ------------------------------------------

class GenericAction(Action): pass # others

class UserAction(Action): pass # card/character skill actions
class BaseAction(UserAction): pass # attack, graze, heal
class SpellCardAction(UserAction): pass

class InternalAction(Action): pass # actions for internal use, should not be intercepted by EHs

# skill action, should follow some conventions.
# skill action should set it's 'cards' attrib to a CardWrapper,
# which has similar attribs like ordinal cards,
# primarily the 'associated_action' attrib.
class SkillAction(Action): pass

class TreatAsAction(SkillAction):
    # treat_as = ......
    def __init__(self, actor, cards):
        self.cards = cards
        self.actor = actor

    def apply_action(self):
        cards = self.cards
        actor = self.actor
        wrapped = self.get_wrapped_card(actor, cards)
        if wrapped:
            self.cards = [wrapped]
            return True
        else:
            self.cards = None
            return False

    @classmethod
    def get_wrapped_card(cls, actor, cards):
        if cls.cond(actor, cards):
            from cards import CardWrapper
            w = CardWrapper.wrap(cards)
            w.associated_action = cls.treat_as.associated_action
            w.target = cls.treat_as.target
            return w
        return None

    @classmethod
    def cond(cls, actor, cards):
        return False

class Damage(GenericAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        target = self.target
        target.life -= self.amount
        if target.life <= 0:
            Game.getgame().emit_event('player_dead', target)
            target.dead = True
        return True

class Attack(BaseAction):

    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = UseGraze(target)
        if not g.process_action(graze_action):
            g.process_action(Damage(source, target, amount=self.damage))
            return True
        else:
            return False

class Heal(BaseAction):

    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        source = self.source # target is ignored
        if source.life < source.maxlife:
            source.life = min(source.life + self.amount, source.maxlife)
            return True
        else:
            return False

class Demolition(SpellCardAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if not len(target.cards): return False

        card = random_choose_card(target)
        self.card = card
        g.players.exclude(target).reveal(card)
        g.process_action(
            DropCards(target=target, cards=[card])
        )
        return True

class Reject(SpellCardAction):
    def __init__(self, source, target_act):
        self.source = source
        self.target_act = target_act

    def apply_action(self):
        if not isinstance(self.target_act, SpellCardAction):
            return False
        self.target_act.cancelled = True
        return True

@register_eh
class RejectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            g = Game.getgame()

            p, input = g.players.user_input_any(
                'choose_card', self._expects, self
            )

            if p:
                sid_list, cid_list = input # TODO: skill
                card, = g.deck.getcards(cid_list) # card was already revealed
                action = Reject(source=p, target_act=act)
                action.associated_card = card
                g.process_action(DropUsedCard(p, [card]))
                g.process_action(action)
        return act

    def _expects(self, p, input):
        from utils import check, CheckFailed
        try:
            check_type([[int, Ellipsis], [int, Ellipsis]], input)

            sid_list, cid_list = input

            g = Game.getgame()
            card, = g.deck.getcards(cid_list)
            check(card in p.cards)

            g.players.exclude(p).reveal(card)

            check(self.cond([card]))
            return True
        except CheckFailed as e:
            import traceback
            traceback.print_exc(e)
            return False

    def cond(self, cardlist):
        from utils import check, CheckFailed
        import cards
        try:
            check(len(cardlist) == 1)
            check(isinstance(cardlist[0], cards.RejectCard))
            return True
        except CheckFailed:
            return False

# ---------------------------------------------------

class DropCards(GenericAction):

    def __init__(self, target, cards):
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = self.cards

        from cards import CardWrapper
        cards = CardWrapper.unwrap(cards)
        self.cards = cards

        tcs = set(target.cards)
        cs = set(cards)
        assert cs.issubset(tcs), 'WTF?!'
        target.cards = list(tcs - cs)

        return True

class DropUsedCard(DropCards): pass

class UseCard(GenericAction):
    def __init__(self, target):
        self.target = target
        # self.cond = __subclass__.cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = user_choose_card(self, target, self.cond)
        if not cards:
            return False
        else:
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

class UseGraze(UseCard):
    def cond(self, cl):
        import cards
        return len(cl) == 1 and isinstance(cl[0], cards.GrazeCard)

class DropCardStage(GenericAction):

    def cond(self, cards):
        t = self.target
        return len(cards) == len(t.cards) - t.life

    def __init__(self, target):
        self.target = target

    def apply_action(self):
        target = self.target
        life = target.life
        n = len(target.cards) - life
        if n<=0:
            return True
        g = Game.getgame()
        cards = user_choose_card(self, target, cond=self.cond)
        if cards:
            g.process_action(DropCards(target, cards=cards))
        else:
            cards = target.cards[:max(n, 0)]
            g.players.exclude(target).reveal(cards)
            g.process_action(DropCards(target, cards=cards))
        return True

class DrawCards(GenericAction):

    def __init__(self, target, amount=2):
        self.target = target
        self.amount = amount

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = g.deck.drawcards(self.amount)

        target.reveal(cards)
        target.cards.extend(cards)
        self.cards = cards
        return True

class DrawCardStage(DrawCards): pass

class LaunchCard(GenericAction):
    def __init__(self, source, target_list, card):
        self.source, self.target_list, self.card = source, target_list, card

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        action = card.associated_action
        g.process_action(DropUsedCard(self.source, cards=[card]))
        if action:
            t = card.target
            if t == 'self':
                target_list = [self.source]
            elif isinstance(t, int):
                target_list = self.target_list
                if len(target_list) != t: return False

            for target in target_list:
                a = action(source=self.source, target=target)
                a.associated_card = card
                g.process_action(a)
            return True
        return False

class ActionStage(GenericAction):

    def __init__(self, target):
        self.actor = target

    def default_action(self):
       return True

    def apply_action(self):
        g = Game.getgame()
        actor = self.actor

        actor.stage = g.ACTION_STAGE

        try:
            while True:
                input = actor.user_input('action_stage_usecard')
                check(input)
                check(isinstance(input, (list, tuple)))

                skill_ids, card_ids, target_list = input

                check(isinstance(skill_ids, (list, tuple)))
                check(isinstance(card_ids, (list, tuple)))
                check(isinstance(target_list, (list, tuple)))

                cards = g.deck.getcards(card_ids)
                check(cards)
                check(set(cards).issubset(set(actor.cards)))

                target_list = [g.player_fromid(i) for i in target_list]
                from game import AbstractPlayer
                check(all(isinstance(p, AbstractPlayer) for p in target_list))

                # skill selected
                if skill_ids:
                    card = skill_wrap(actor, skill_ids, cards)
                    check(card)

                else:
                    check(len(cards) == 1)
                    card = cards[0]

                g.players.exclude(actor).reveal(card)
                g.process_action(LaunchCard(actor, target_list, card))

        except CheckFailed as e:
            try:
                import traceback
                traceback.print_exc(e)
                print skill_ids, card_ids, target_list
            except:
                pass

        actor.stage = g.NORMAL
        return True
