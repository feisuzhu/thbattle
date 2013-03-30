# All generic and cards' Actions, EventHandlers are here
# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, PlayerList, sync_primitive

from network import Endpoint
import random

from functools import wraps
from collections import defaultdict

from utils import check, check_type, CheckFailed, BatchList, group_by

import logging
log = logging.getLogger('THBattle_Actions')

# ------------------------------------------
# aux functions

def _get_hooktable():
    g = Game.getgame()
    hooktable = getattr(g, '_hooktable', None)
    if hooktable is None:
        hooktable = defaultdict(list)
        g._hooktable = hooktable

    return hooktable


def hookable(func):
    @wraps(func)
    def hooker(*args, **kwargs):
        hooks = _get_hooktable()[func]
        if not hooks:
            return func(*args, **kwargs)
        else:
            return hooks[-1](func, *args, **kwargs)

    def hook(hookfunc):
        _get_hooktable()[func].append(hookfunc)

    def unhook(hookfunc=None):
        _get_hooktable()[func].remove(hookfunc)

    hooker.hook = hook
    hooker.unhook = unhook
    return hooker


def user_choose_cards_logic(input, act, target, categories=None):
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
            check(all(c.resides_in.owner is target for c in cards)) # Cards belong to target?

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
    return user_choose_cards_logic(input, act, target, categories)


def user_choose_players_logic(input, act, target, candidates):
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
    return user_choose_players_logic(input, act, target, candidates)


def user_choose_cards_and_players(act, target, categories=None, candidates=[]):
    input = target.user_input('choose_card_and_player', (act, candidates))
    cards = user_choose_cards_logic(input, act, target, categories)
    if not cards: return None
    pl = user_choose_players_logic(input, act, target, candidates)
    if not pl: return None
    return (cards, pl)


def random_choose_card(categories):
    from itertools import chain
    allcards = list(chain.from_iterable(categories))
    if not allcards:
        return None

    g = Game.getgame()
    c = g.random.choice(allcards)
    v = sync_primitive(c.syncid, g.players)
    cl = g.deck.lookupcards([v])
    if len(cl)!=1:
        print cl
    assert len(cl) == 1
    return cl[0]


def skill_wrap(actor, sid_list, cards):
    g = Game.getgame()
    try:
        check(all(c.resides_in.owner is actor for c in cards))
        for skill_id in sid_list:
            check(isinstance(skill_id, int))
            check(0 <= skill_id < len(actor.skills))

            skill_cls = actor.skills[skill_id]

            if not getattr(skill_cls, 'no_reveal', False):
                g.players.exclude(actor).reveal(cards)

            card = skill_cls.wrap(cards, actor)

            check(card.check())

            g.deck.register_vcard(card)

            cards = [card]

        #migrate_cards(cards, actor.cards, False, True)
        cards[0].move_to(actor.cards)

        return cards[0]
    except CheckFailed as e:
        return None


def shuffle_here():
    from .cards import CardList, VirtualCard
    g = Game.getgame()
    g.emit_event('shuffle_cards', True)
    for p in g.players:
        assert all([
            not c.is_card(VirtualCard)
            for c in p.cards
        ]), 'VirtualCard in handcard of %s !!!' % repr(p)

        g.deck.shuffle(p.cards)


def migrate_cards(cards, to, unwrap=False, no_event=False):
    g = Game.getgame()
    from .cards import VirtualCard
    groups = group_by(cards, lambda c: c if c.is_card(VirtualCard) else c.resides_in)

    for l in groups:
        cl = l[0].resides_in
        for c in l:
            if unwrap and c.is_card(VirtualCard):
                c.move_to(None)
                migrate_cards(
                    c.associated_cards,
                    to,
                    unwrap != migrate_cards.SINGLE_LAYER,
                    no_event
                )
            else:
                c.move_to(to)
                if c.is_card(VirtualCard):
                    assert c.resides_in.owner
                    sp = c.resides_in.owner.special
                    migrate_cards(c.associated_cards, sp, False, no_event)

        if not no_event:
            act = g.action_stack[-1]
            g.emit_event('card_migration', (act, l, cl, to)) # (action, cardlist, from, to)

migrate_cards.SINGLE_LAYER = 2


def choose_peer_card_logic(input, source, target, categories):
    assert all(c.owner is target for c in categories)
    try:
        check(sum(len(c) for c in categories)) # no cards at all

        cid = input
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


@hookable
def choose_peer_card(source, target, categories):
    cid = source.user_input('choose_peer_card', (target, categories))
    return choose_peer_card_logic(cid, source, target, categories)


def choose_individual_card_logic(input, source, cards):
    try:
        cid = input
        g = Game.getgame()

        check(isinstance(cid, int))

        cards = [c for c in cards if c.syncid == cid]

        check(len(cards)) # Invalid id

        return cards[0]

    except CheckFailed:
        return None


@hookable
def choose_individual_card(source, cards):
    cid = source.user_input('choose_individual_card', cards)
    return choose_individual_card_logic(cid, source, cards)


@hookable
def user_choose_option(act, tgt):
    return tgt.user_input('choose_option', act)


action_eventhandlers = set()
def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls

# ------------------------------------------

class GenericAction(Action): pass
class LaunchCardAction: pass

class UserAction(Action): # card/character skill actions
    def is_valid(self):
        if getattr(self, '_force_fire', False):
            return True

        if self.source and self.source.dead:
            return False

        if self.target and self.target.dead:
            return False

        return True

    def force_fire(self):
        # Fire action regardless player status
        # for Exinwan only, do not use on other purpose
        self._force_fire = True


class PlayerDeath(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.dead = True
        src = self.source or self.target
        others = g.players.exclude(tgt)
        from .cards import VirtualCard
        from .actions import DropCards
        lists = [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell, tgt.special]
        lists.extend(tgt.showncardlists)
        for cl in lists:
            if not cl: continue
            others.reveal(list(cl))
            g.process_action(DropCards(tgt, cl))
            assert not cl

        tgt.skills[:] = []
        return True


class PlayerRevive(GenericAction):
    def __init__(self, source, target, hp):
        self.source = source
        self.target = target
        self.hp = hp

    def apply_action(self):
        tgt = self.target
        assert tgt.dead

        tgt.dead = False
        tgt.maxlife = tgt.__class__.maxlife
        tgt.skills = list(tgt.__class__.skills)

        tgt.life = min(tgt.maxlife, self.hp)
        return True

    def is_valid(self):
        return self.target.dead


class TryRevive(GenericAction):
    def __init__(self, target, dmgact):
        self.source = self.target = target
        self.dmgact = dmgact
        g = Game.getgame()
        if target.dead:
            log.error('TryRevive buggy condition, __init__')
            return
        self.asklist = BatchList(
            p for p in g.players if not p.dead
        ).rotate_to(target)

    def apply_action(self):
        tgt = self.target
        if tgt.tags['in_tryrevive']:
            # nested TryRevive, just return True
            # will trigger when Eirin uses Diamond Exinwan to heal self
            return True

        if tgt.dead:
            log.error('TryRevive buggy condition, apply')
            import traceback
            traceback.print_stack()
            return False

        tgt.tags['in_tryrevive'] = True
        g = Game.getgame()
        pl = self.asklist
        from .cards import LaunchHeal
        for p in pl:
            while True:
                act = LaunchHeal(p, tgt)
                if g.process_action(act):
                    cards = act.cards
                    if not cards: continue
                    from .cards import Heal
                    g.process_action(Heal(p, tgt))
                    if tgt.life > 0:
                        tgt.tags['in_tryrevive'] = False
                        return True
                    continue
                break
        tgt.tags['in_tryrevive'] = False
        return tgt.life > 0

    def is_valid(self):
        tgt = self.target
        return not tgt.dead and tgt.maxlife > 0


class BaseDamage(GenericAction):
    def __init__(self, source, target, amount=1):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.life -= self.amount
        return True


class Damage(BaseDamage):
    pass


class LifeLost(BaseDamage):
    pass


class MaxLifeChange(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount
        
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.maxlife += self.amount
        if not tgt.maxlife:
            g.process_action(PlayerDeath(None, tgt))
            return True
            
        if tgt.life > tgt.maxlife:
            tgt.life = tgt.maxlife
            
        return True

        
# ---------------------------------------------------

class DropCards(GenericAction):
    def __init__(self, target, cards):
        self.target = target
        self.cards = cards
        g = Game.getgame()
        self.source = g.action_stack[-1].source

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

    def is_valid(self):
        return True


class DropUsedCard(DropCards):
    pass


class UseCard(UserAction):
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

    def cond(self, cards):
        t = self.target
        if not len(cards) == self.dropn:
            return False

        if not all(c.resides_in in (t.cards, t.showncards) for c in cards):
            return False

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

    def is_valid(self):
        return not self.target.dead


class DrawCardStage(DrawCards):
    pass


class LaunchCard(GenericAction, LaunchCardAction):
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
            a.force_fire()  # For Exinwan, see UserAction.force_fire
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

        if not self.validate_distance():
            log.debug('LaunchCard: does not fulfill distance constraint')
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

    def validate_distance(self):
        dist = self.calc_base_distance()
        g = Game.getgame()

        g.emit_event('calcdistance', (self, dist))
        card_dist = getattr(self.card, 'distance', 1000)
        for p in dist:
            dist[p] -= card_dist
        g.emit_event('post_calcdistance', (self, dist))

        return all([dist[p] <= 0 for p in self.target_list])

    def calc_base_distance(self):
        g = Game.getgame()
        pl = [p for p in g.players if not p.dead]
        src = self.source
        loc = pl.index(src)
        n = len(pl)
        dist = {
            p: min(abs(i), n-abs(i))
            for p, i in zip(pl, xrange(-loc, -loc+n))
        }
        return dist


class ActionStageLaunchCard(LaunchCard):
    pass


class ActionStage(GenericAction):

    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if target.dead: return False

        shuffle_here()

        try:
            while not target.dead:
                g.emit_event('action_stage_action', target)
                input = target.user_input('action_stage_usecard')
                check_type([[int, Ellipsis]] * 3, input)

                skill_ids, card_ids, target_list = input

                if card_ids:
                    cards = g.deck.lookupcards(card_ids)
                    check(cards)
                    check(all(c.resides_in.owner is target for c in cards))
                else:
                    cards = []

                target_list = [g.player_fromid(i) for i in target_list]
                from game import AbstractPlayer
                check(all(isinstance(p, AbstractPlayer) for p in target_list))

                # skill selected
                if skill_ids:
                    card = skill_wrap(target, skill_ids, cards)
                    check(card)
                else:
                    check(len(cards) == 1)
                    g.players.exclude(target).reveal(cards)
                    card = cards[0]
                    from .cards import HiddenCard
                    assert not card.is_card(HiddenCard)
                    check(card.resides_in in (target.cards, target.showncards))
                if not g.process_action(ActionStageLaunchCard(target, target_list, card)):
                    # invalid input
                    log.debug('ActionStage: LaunchCard failed.')
                    break

                shuffle_here()

        except CheckFailed as e:
            pass

        return True


class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if target.dead: return False
        ft_cards = target.fatetell
        for card in reversed(list(ft_cards)):  # what comes last, launches first.
            if not target.dead:
                g.process_action(LaunchFatetellCard(target, card))

        return True


class BaseFatetell(GenericAction):
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


class Fatetell(BaseFatetell):
    pass


class TurnOverCard(BaseFatetell):
    pass


class FatetellAction(GenericAction): pass


class LaunchFatetellCard(FatetellAction):
    def __init__(self, target, card):
        self.source = target
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        card = self.card
        act = card.delayed_action
        assert act
        a = act(source=card.fatetell_source, target=target)
        a.associated_card = card
        g.process_action(a)
        a.fatetell_postprocess()
        return True


class ForEach(UserAction):
    # action_cls == __subclass__.action_cls
    include_dead = False
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
            if t.dead and not self.include_dead:
                continue
            a = self.action_cls(source, t)
            a.associated_card = card
            a.parent_action = self
            g.process_action(a)
        self.cleanup()
        return True


class PlayerTurn(GenericAction):
    def __init__(self, target):
        self.source = self.target = target

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        p.tags['turn_count'] += 1
        g.current_turn = p

        g.process_action(FatetellStage(p))
        g.process_action(DrawCardStage(p))
        g.process_action(ActionStage(p))
        g.process_action(DropCardStage(p))

        return True


class DummyAction(GenericAction):
    def __init__(self, source, target, result=True):
        self.source, self.target, self.result = \
            source, target, result

    def apply_action(self):
        return self.result


class RevealIdentity(GenericAction):
    def __init__(self, target, to):
        self.target = target
        self.to = to

    def apply_action(self):
        tgt = self.target
        self.to.reveal(tgt.identity)
        return True


class Pindian(UserAction):
    no_reveal = True

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        pl = PlayerList([src, tgt])
        cl = [None, None]

        def process(p, input):
            card = user_choose_cards_logic(input, self, p, [p.cards, p.showncards])
            if not card:
                card = random_choose_card([p.cards, p.showncards])
            else:
                card = card[0]

            cl[pl.index(p)] = card
            g.emit_event('pindian_card_chosen', (p, card))

            return card

        pl.user_input_all('choose_card_and_player', process, (self, []))

        g.players.reveal(cl)
        g.process_action(DropCards(pl[0], [cl[0]]))
        g.process_action(DropCards(pl[1], [cl[1]]))

        return cl[0].number > cl[1].number

    @staticmethod
    def cond(cl):
        from .cards import CardList
        return len(cl) == 1 and cl[0].resides_in.type in ('handcard', 'showncard')

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.dead or tgt.dead: return False
        if not (src.cards or src.showncards): return False
        if not (tgt.cards or tgt.showncards): return False
        return True


@register_eh
class DyingHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, (BaseDamage, MaxLifeChange)): return act

        tgt = act.target
        if tgt.dead or tgt.life > 0: return act

        g = Game.getgame()
        if g.process_action(TryRevive(tgt, dmgact=act)):
            return act

        src = act.source if isinstance(act, Damage) else None

        g.process_action(PlayerDeath(src, tgt))

        if tgt is g.current_turn:
            for a in reversed(g.action_stack):
                if isinstance(a, UserAction):
                    a.interrupt_after_me()

        return act
