# All generic and cards' Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, SyncPrimitive

from network import Endpoint
import random

from utils import check, check_type, CheckFailed

import logging
log = logging.getLogger('THBattle_Actions')

# ------------------------------------------
# aux functions
def user_choose_card(act, target, cond):
    from utils import check, CheckFailed
    g = Game.getgame()
    input = target.user_input('choose_card', act) # list of card ids

    try:
        check_type([[int, Ellipsis], [int, Ellipsis]], input)

        sid_list, cid_list = input

        cards = g.deck.lookupcards(cid_list)
        cs = set(cards)

        check(len(cs) == len(cid_list)) # repeated ids

        check(cs.issubset(set(target.cards))) # Whose cards?! Wrong ids?!

        g.players.exclude(target).reveal(cards)

        if sid_list:
            cards = skill_wrap(target, sid_list, cards)

        check(cond(cards))

        return cards
    except CheckFailed as e:
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

            skill_cls = actor.skills[skill_id]
            card = skill_cls(actor, cards)

            check(card.check())

            cards = [card]

        card = cards[0]
        return card
    except CheckFailed as e:
        return None

def validate_distance(calc, card, source, target_list):
    try:
        dist = card.distance
    except AttributeError:
        # no distance constraint
        return [True] * len(target_list)

    lookup = calc.distance
    c = calc.correction

    return [
        lookup[t] - (dist + c) <= 0
        for t in target_list
    ]

def migrate_cards(cards, to):
    g = Game.getgame()
    mapping = {}
    for c in cards:
        l = mapping.setdefault(id(c.resides_in), [])
        l.append(c)

    act = g.action_stack[0]

    for l in mapping.values():
        cl = l[0].resides_in
        g.emit_event('card_migration', (act, l, cl, to)) # (action, cardlist, from, to)

        for c in l:
            c.move_to(to)


action_eventhandlers = set()
def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls

# ------------------------------------------

class GenericAction(Action): pass # others
class UserAction(Action): pass # card/character skill actions
class InternalAction(Action): pass # actions for internal use

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

# ---------------------------------------------------

class DropCards(GenericAction):

    def __init__(self, target, cards):
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = self.cards

        from ..characters import Skill
        self.cards = cards = Skill.unwrap(cards)

        assert all(c.resides_in.owner == target for c in cards), 'WTF?!'
        migrate_cards(cards, g.deck.droppedcards)

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
        from .. import cards
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
        self.cards = cards
        return True

class DrawCards(GenericAction):

    def __init__(self, target, amount=2):
        self.target = target
        self.amount = amount

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = g.deck.getcards(self.amount)

        target.reveal(cards)
        migrate_cards(cards, target.cards)
        self.cards = cards
        return True

class DrawCardStage(DrawCards): pass

class LaunchCard(GenericAction):
    def __init__(self, source, target_list, card):
        t = card.target
        if t == 'self':
            target_list = [source]
        elif isinstance(t, int):
            if len(target_list) != t:
               card = None # Incorrect target_list
        self.source, self.target_list, self.card = source, target_list, card

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        target_list = self.target_list
        if not card: return False
        action = card.associated_action
        g.process_action(DropUsedCard(self.source, cards=[card]))
        if action:
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
                check_type([[int, Ellipsis]] * 3, input)

                skill_ids, card_ids, target_list = input

                cards = g.deck.lookupcards(card_ids)
                check(cards)
                check(set(cards).issubset(set(actor.cards)))

                target_list = [g.player_fromid(i) for i in target_list]
                from game import AbstractPlayer
                check(all(isinstance(p, AbstractPlayer) for p in target_list))

                g.players.exclude(actor).reveal(cards)

                # skill selected
                if skill_ids:
                    card = skill_wrap(actor, skill_ids, cards)
                    check(card)

                else:
                    check(len(cards) == 1)
                    card = cards[0]

                if not g.process_action(LaunchCard(actor, target_list, card)):
                    # invalid input
                    break

        except CheckFailed as e:
            pass

        actor.stage = g.NORMAL
        return True

class CalcDistance(InternalAction):
    def __init__(self, source):
        self.source = source
        self.distance = None
        self.correction = 0

    def apply_action(self):
        g = Game.getgame()
        pl = g.players
        source = self.source
        loc = pl.index(source)
        n = len(pl)
        self.distance = {
            p: min(abs(i), n-abs(i))
            for p, i in zip(pl, xrange(-loc, -loc+n))
        }
        return True

@register_eh
class DistanceValidator(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire' and isinstance(arg[0], LaunchCard):
            act = arg[0]
            g = Game.getgame()
            calc = CalcDistance(act.source)
            g.process_action(calc)
            if not all(validate_distance(calc, act.card, act.source, act.target_list)):
                return (act, False)

        return arg

class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        ft_cards = target.fatetell
        for card in reversed(ft_cards[:]): #what comes last, launches first.
            act = card.associated_action
            assert act
            a = act(source=target, target=target) # FIXME: make it LaunchFatetellCard
            a.associated_card = card
            g.process_action(a)

        return True

class Fatetell(GenericAction):
    def __init__(self, target, cond):
        self.target = target
        self.cond = cond

    def apply_action(self):
        g = Game.getgame()
        card, = g.deck.getcards(1)
        g.players.reveal(card)
        self.card = card
        migrate_cards([card], g.deck.droppedcards)
        if self.cond(card):
            return True
        return False
