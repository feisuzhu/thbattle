# All generic and cards' Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, sync_primitive

from network import Endpoint
import random

from utils import check, check_type, CheckFailed, BatchList

import logging
log = logging.getLogger('THBattle_Actions')

# ------------------------------------------
# aux functions

def _user_choose_cards_logic(input, act, target, categories=None):
    from utils import check, CheckFailed
    g = Game.getgame()

    try:
        check_type([[int, Ellipsis]] * 3, input)

        sid_list, cid_list, pid_list = input

        cards = g.deck.lookupcards(cid_list)
        check(len(cards) == len(cid_list)) # Invalid id

        cs = set(cards)
        check(len(cs) == len(cid_list)) # repeated ids

        if not categories:
            categories = [target.cards, target.showncards]

        if sid_list:
            check(all(cat.owner is target for cat in categories))

            # associated_cards will be revealed here
            c = skill_wrap(target, sid_list, cards)
            check(c)
            cards = [c]
        else:
            check(all(c.resides_in in categories for c in cards)) # Cards in desired categories?
            if not getattr(act, 'no_reveal', False):
                g.players.exclude(target).reveal(cards)

        check(act.cond(cards))

        return cards
    except CheckFailed as e:
        return None

def user_choose_cards(act, target, categories=None):
    input = target.user_input('choose_card_and_player', (act, [])) # list of card ids
    return _user_choose_cards_logic(input, act, target, categories)

def _user_choose_players_logic(input, act, target, candidates):
    try:
        g = Game.getgame()
        check_type([[int, Ellipsis]] * 3, input)
        _, _, pids = input
        check(pids)
        pl = [g.player_fromid(i) for i in pids]
        from game import AbstractPlayer
        check(all(p in candidates for p in pl))
        pl, valid = act.choose_player_target(pl)
        check(valid)
        return pl
    except CheckFailed:
        return None

def user_choose_players(act, target, candidates):
    input = target.user_input('choose_card_and_player', (act, candidates))
    return _user_choose_players_logic(input, act, target, candidates)

def user_choose_cards_and_players(act, target, categories=None, candidates=[]):
    input = target.user_input('choose_card_and_player', (act, candidates))
    cards = _user_choose_cards_logic(input, act, target, categories)
    if not cards: return None
    pl = _user_choose_players_logic(input, act, target, candidates)
    if not pl: return None
    return (cards, pl)

def random_choose_card(categories):
    from itertools import chain
    allcards = list(chain.from_iterable(categories))
    if not allcards:
        return None
    c = random.choice(allcards)
    g = Game.getgame()
    v = sync_primitive(c.syncid, g.players)
    cl = g.deck.lookupcards([v])
    if len(cl)!=1:
        print cl
    assert len(cl) == 1
    return cl[0]

def skill_wrap(actor, sid_list, cards):
    g = Game.getgame()
    try:
        for skill_id in sid_list:
            check(isinstance(skill_id, int))
            check(0 <= skill_id < len(actor.skills))

            skill_cls = actor.skills[skill_id]

            if not getattr(skill_cls, 'no_reveal', False):
                g.players.exclude(actor).reveal(cards)

            card = skill_cls.wrap(cards, actor)

            check(card.check())

            card.syncid = g.get_synctag()
            g.deck.register_vcard(card)

            cards = [card]

        #migrate_cards(cards, actor.cards, False, True)
        cards[0].move_to(actor.cards)

        return cards[0]
    except CheckFailed as e:
        return None

def shuffle_here():
    from .cards import CardList
    g = Game.getgame()
    g.emit_event('shuffle_cards', True)
    for p in g.players:
        if p.need_shuffle:
            g.deck.shuffle(p.cards)
            p.need_shuffle = False

def migrate_cards(cards, to, unwrap=False, no_event=False):
    g = Game.getgame()
    mapping = {}
    from .cards import VirtualCard
    for c in cards:
        l = mapping.setdefault(id(c) if c.is_card(VirtualCard) else id(c.resides_in), [])
        l.append(c)

    act = g.action_stack[-1]

    for l in mapping.values():
        cl = l[0].resides_in
        for c in l:
            if unwrap and c.is_card(VirtualCard):
                migrate_cards(c.associated_cards, to, True, no_event)
                c.move_to(None)
            else:
                c.move_to(to)
                if c.is_card(VirtualCard):
                    assert c.resides_in.owner
                    sp = c.resides_in.owner.special
                    migrate_cards(c.associated_cards, sp, False, no_event)

        if not no_event:
            g.emit_event('card_migration', (act, l, cl, to)) # (action, cardlist, from, to)

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

class PlayerDeath(GenericAction):
    # dummy, implemented in Game
    pass

class TryRevive(GenericAction):
    # dummy, implemented in Game
    pass

class Damage(GenericAction):
    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.life -= self.amount
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
        #self.cards_before_unwrap = cards

        #migrate_cards([c for c in cards if c.is_card(VirtualCard)], None)

        #self.cards = cards = VirtualCard.unwrap(cards)
        self.cards = cards

        assert all(c.resides_in.owner in (target, None) for c in cards), 'WTF?!'
        migrate_cards(cards, g.deck.droppedcards, unwrap=True)

        return True

class DropUsedCard(DropCards): pass

class UseCard(GenericAction):
    def __init__(self, target):
        self.source = self.target = target
        # self.cond = __subclass__.cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = user_choose_cards(self, target)
        if not cards:
            self.cards = []
            return False
        else:
            self.cards = cards
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

class DropCardStage(GenericAction):

    def cond(self, cards):
        t = self.target
        if not len(cards) == self.dropn:
            return False

        if not all(c.resides_in in (t.cards, t.showncards) for c in cards):
            return False

        return True

    def __init__(self, target):
        self.source = self.target = target
        self.dropn = len(target.cards) + len(target.showncards) - target.life

    def apply_action(self):
        target = self.target
        if target.dead: return False
        life = target.life
        n = self.dropn
        if n<=0:
            return True
        g = Game.getgame()
        cards = user_choose_cards(self, target)
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
        self.source = self.target = target
        self.amount = amount

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        cards = g.deck.getcards(self.amount)

        target.reveal(cards)
        migrate_cards(cards, target.cards)
        self.cards = cards
        return True

class DrawCardStage(DrawCards):
    def apply_action(self):
        t = self.target
        if t.dead: return False
        return DrawCards.apply_action(self)

class BaseLaunchCard(GenericAction):
    pass

class LaunchCard(BaseLaunchCard):
    def __init__(self, source, target_list, card):
        tl, tl_valid = card.target(Game.getgame(), source, target_list)
        self.source, self.target_list, self.card, self.tl_valid = source, tl, card, tl_valid
        self.target = target_list[0] if target_list else source

    def apply_action(self):
        g = Game.getgame()
        card = self.card
        target_list = self.target_list
        if not card: return False

        # special case for debug
        from .cards import HiddenCard
        if card.is_card(HiddenCard):
            raise GameError('launch hidden card')
        # ----------------------

        action = card.associated_action
        if not getattr(card, 'no_drop', False):
            g.process_action(DropUsedCard(self.source, cards=[card]))

        if action:
            target = target_list[0] if target_list else self.source
            a = action(source=self.source, target=target)
            self.card_action = a
            a.associated_card = card
            a.target_list = target_list
            g.process_action(a)
            return True
        return False

    def is_valid(self):
        if not self.tl_valid:
            log.debug('LaunchCard.tl_valid FALSE')
            return False
        g = Game.getgame()
        card = self.card
        if not card:
            log.debug('LaunchCard.card FALSE')
            return False

        cls = card.associated_action
        src = self.source

        tl = self.target_list
        target = tl[0] if tl else src
        act = cls(source=src, target=target)
        act.associated_card = card
        act.target_list = tl
        if not act.can_fire():
            log.debug('LaunchCard card_action.can_fire() FALSE')
            return False

        return True

class ActionStage(GenericAction):

    def __init__(self, target):
        self.actor = target

    def apply_action(self):
        g = Game.getgame()
        actor = self.actor
        if actor.dead: return False

        shuffle_here()

        try:
            while not actor.dead:
                g.emit_event('action_stage_action', self)
                input = actor.user_input('action_stage_usecard')
                check_type([[int, Ellipsis]] * 3, input)

                skill_ids, card_ids, target_list = input

                if card_ids:
                    cards = g.deck.lookupcards(card_ids)
                    check(cards)
                    check(all(c.resides_in.owner is actor for c in cards))
                else:
                    cards = []

                target_list = [g.player_fromid(i) for i in target_list]
                from game import AbstractPlayer
                check(all(isinstance(p, AbstractPlayer) for p in target_list))

                # skill selected
                if skill_ids:
                    card = skill_wrap(actor, skill_ids, cards)
                    check(card)
                else:
                    check(len(cards) == 1)
                    g.players.exclude(actor).reveal(cards)
                    card = cards[0]
                    from .cards import HiddenCard
                    assert not card.is_card(HiddenCard)
                    check(card.resides_in in (actor.cards, actor.showncards))
                if not g.process_action(LaunchCard(actor, target_list, card)):
                    # invalid input
                    log.debug('ActionStage: LaunchCard failed.')
                    break

                shuffle_here()

        except CheckFailed as e:
            pass

        return True

class CalcDistance(InternalAction):
    def __init__(self, source, card):
        self.source = source
        self.distance = None
        self.correction = 0
        self._force_valid = False
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        pl = [p for p in g.players if not p.dead]
        self.player_list = pl
        source = self.source
        loc = pl.index(source)
        n = len(pl)
        raw = self.raw_distance = {
            p: min(abs(i), n-abs(i))
            for p, i in zip(pl, xrange(-loc, -loc+n))
        }
        self.distance = dict(raw)
        return True

    def force_valid(self):
        self._force_valid = True

    def validate(self):
        g = Game.getgame()
        pl = self.player_list
        lookup = self.distance
        c = self.correction
        if not self._force_valid:
            try:
                dist = self.card.distance

                return {
                    t: lookup[t] - (dist + c) <= 0
                    for t in pl
                }
            except AttributeError:
                pass

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
                log.debug('REJECTED due to distance constraint.')
                return (act, False)

        return arg

class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if target.dead: return False
        ft_cards = target.fatetell
        for card in reversed(list(ft_cards)): #what comes last, launches first.
            if not target.dead:
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
        return True

    @property
    def succeeded(self):
        return self.cond(self.card)

class FatetellAction(UserAction): pass

class LaunchFatetellCard(BaseLaunchCard, FatetellAction):
    def __init__(self, target, card):
        self.source = target
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        card = self.card
        act = card.associated_action
        assert act
        a = act(source=card.fatetell_source, target=target)
        a.associated_card = card
        g.process_action(a)
        a.fatetell_postprocess()
        return True

class ForEach(GenericAction):
    # action_cls == __subclass__.action_cls
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

class PlayerTurn(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        p.tags['turn_count'] += 1
        g.current_turn = p
        if not p.dead: g.process_action(FatetellStage(p))
        if not p.dead: g.process_action(DrawCardStage(p))
        if not p.dead: g.process_action(ActionStage(p))
        if not p.dead: g.process_action(DropCardStage(p))
        return True

class DummyAction(GenericAction):
    def __init__(self, source, target, result=True):
        self.source, self.target, self.result = \
            source, target, result

    def apply_action(self):
        return self.result

class SkillAwake(GenericAction):
    skill = None
    def apply_action(self):
        s = self.skill
        assert s
        self.target.skills.append(s)
        return True

class RevealIdentity(GenericAction):
    def __init__(self, target, to):
        self.target = target
        self.to = to

    def apply_action(self):
        tgt = self.target
        self.to.reveal(tgt.identity)
        return True
