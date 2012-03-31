# All generic and cards' Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, SyncPrimitive

from network import Endpoint
import random

from utils import check, check_type, CheckFailed, BatchList

import logging
log = logging.getLogger('THBattle_Actions')

# ------------------------------------------
# aux functions
def user_choose_card(act, target, cond, categories=None):
    from utils import check, CheckFailed
    g = Game.getgame()
    input = target.user_input('choose_card', act) # list of card ids

    try:
        check_type([[int, Ellipsis], [int, Ellipsis]], input)

        sid_list, cid_list = input


        cards = g.deck.lookupcards(cid_list)
        check(len(cards) == len(cid_list)) # Invalid id

        cs = set(cards)
        check(len(cs) == len(cid_list)) # repeated ids

        check(all(c.resides_in.owner is target for c in cards)) # Whose cards?!

        if not categories:
            categories = [target.cards, target.showncards]

        check(all(c.resides_in in categories for c in cards)) # Cards in desired categories?

        g.players.exclude(target).reveal(cards)

        if sid_list:
            cards = skill_wrap(target, sid_list, cards)

        check(cond(cards))

        return cards
    except CheckFailed as e:
        return None

def random_choose_card(categories):
    from itertools import chain
    allcards = list(chain.from_iterable(categories))
    if not allcards:
        return None
    c = random.choice(allcards)
    v = SyncPrimitive(c.syncid)
    g = Game.getgame()
    g.players.reveal(v)
    v = v.value
    cl = g.deck.lookupcards([v])
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

def choose_peer_card(source, target, categories):
    assert all(c.owner is target for c in categories)
    try:
        check(sum(len(c) for c in categories)) # no cards at all

        cid = source.user_input('choose_peer_card', (target, categories))
        g = Game.getgame()

        check(isinstance(cid, int))

        cards = g.deck.lookupcards((cid,))

        check(len(cards) == 1) # Invalid id
        card = cards[0]

        check(card.resides_in.owner is target)
        check(card.resides_in in categories)

        return card

    except CheckFailed:
        return None

def choose_individual_card(source, cards):
    try:
        cid = source.user_input('choose_individual_card', cards)
        g = Game.getgame()

        check(isinstance(cid, int))

        cards = [c for c in cards if c.syncid == cid]

        check(len(cards)) # Invalid id

        return cards[0]

    except CheckFailed:
        return None

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

        from .cards import VirtualCard
        self.cards = cards = VirtualCard.unwrap(cards)

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
            self.associated_cards = []
            return False
        else:
            self.associated_cards = cards
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

class DropCardStage(GenericAction):

    def cond(self, cards):
        t = self.target
        if not len(cards) == len(t.cards) + len(t.showncards) - t.life:
            return False

        if not all(c.resides_in in (t.cards, t.showncards) for c in cards):
            return False

        return True

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
            from itertools import chain
            cards = list(chain(target.cards, target.showncards))[min(-n, 0):]
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
        tl, tl_valid = card.target(Game.getgame(), source, target_list)
        if not tl_valid:
            card = None # Incorrect target_list
        self.source, self.target_list, self.card = source, tl, card

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        target_list = self.target_list
        if not card: return False
        action = card.associated_action
        g.process_action(DropUsedCard(self.source, cards=[card]))
        if action:
            target = target_list[0] if len(target_list) == 1 else None
            a = action(source=self.source, target=target)
            a.associated_card = card
            a.target_list = target_list
            g.process_action(a)
            return True
        return False

    def is_valid(self):
        g = Game.getgame()
        card = self.card
        if not card: return False
        cls = card.associated_action
        src = self.source
        for t in self.target_list:
            act = cls(source=src, target=t)
            act.associated_card = card
            if not act.is_valid():
                return False
        return True

class ActionStage(GenericAction):

    def __init__(self, target):
        self.actor = target

    def apply_action(self):
        g = Game.getgame()
        actor = self.actor

        actor.stage = g.ACTION_STAGE

        try:
            while True:
                g.emit_event('action_stage_action', self)
                input = actor.user_input('action_stage_usecard')
                check_type([[int, Ellipsis]] * 3, input)

                skill_ids, card_ids, target_list = input

                cards = g.deck.lookupcards(card_ids)
                check(cards)
                check(all(c.resides_in.owner is actor for c in cards))

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
                    check(card.resides_in in (actor.cards, actor.showncards))

                if not g.process_action(LaunchCard(actor, target_list, card)):
                    # invalid input
                    break

        except CheckFailed as e:
            pass

        actor.stage = g.NORMAL
        return True

class CalcDistance(InternalAction):
    def __init__(self, source, card):
        self.source = source
        self.distance = None
        self.correction = 0
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        pl = g.players
        source = self.source
        loc = pl.index(source)
        n = len(pl)
        raw = self.raw_distance = {
            p: min(abs(i), n-abs(i))
            for p, i in zip(pl, xrange(-loc, -loc+n))
        }
        self.distance = dict(raw)
        return True

    def validate(self):
        g = Game.getgame()
        pl = g.players
        lookup = self.distance
        c = self.correction
        try:
            dist = self.card.distance

            return {
                t: lookup[t] - (dist + c) <= 0
                for t in pl
            }
        except AttributeError:
            return {
                t: True
                for t in pl
            }

@register_eh
class DistanceValidator(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire' and isinstance(arg[0], LaunchCard):
            g = Game.getgame()
            act = arg[0]
            card = act.card
            dist = getattr(card, 'distance', None)
            if dist is None:
                # no distance constraint
                return arg
            calc = CalcDistance(act.source, card)
            g.process_action(calc)
            rst = calc.validate()
            if not all(rst[t] for t in act.target_list):
                return (act, False)

        return arg

class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        ft_cards = target.fatetell
        for card in reversed(list(ft_cards)): #what comes last, launches first.
            g.process_action(LaunchFatetellCard(target, card))

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

class FatetellAction(UserAction): pass

class LaunchFatetellCard(FatetellAction):
    def __init__(self, target, card):
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        card = self.card
        act = card.associated_action
        assert act
        a = act(source=target, target=target)
        a.associated_card = card
        g.process_action(a)
        a.fatetell_postprocess()
        return True

class ForEach(GenericAction):
    def prepare(self):
        pass

    def cleanup(self):
        pass

    def __init__(self, source, target):
        self.source = source
        self.target = None

    def apply_action(self):
        tl = self.target_list
        source = self.source
        card = self.associated_card
        g = Game.getgame()
        self.prepare()
        for t in tl:
            a = self.action_cls(source, t)
            a.associated_card = card
            a.parent_action = self
            g.process_action(a)
        self.cleanup()
        return True
