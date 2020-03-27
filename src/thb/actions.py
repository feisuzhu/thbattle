# -*- coding: utf-8 -*-

# -- stdlib --
from collections import OrderedDict, defaultdict
from copy import copy
import logging

# -- third party --
# -- own --
from game.autoenv import Action, ActionShootdown, EventHandler, EventHandlerGroup, Game
from game.autoenv import GameException, InputTransaction, sync_primitive, user_input
from thb.inputlets import ActionInputlet, ChoosePeerCardInputlet
from utils import BatchList, CheckFailed, check, check_type, group_by


# -- code --
log = logging.getLogger('THBattle_Actions')


# ------------------------------------------
# aux functions
def mark(act, tag, v=True):
    setattr(act, '_tag_' + tag, v)


def marked(act, tag):
    return getattr(act, '_tag_' + tag, None)


def ttags(actor):
    tags = actor.tags
    tc = tags['turn_count']
    return tags.setdefault('turn_tags:%s' % tc, defaultdict(int))


def ask_for_action(initiator, actors, categories, candidates, timeout=None, trans=None):
    # initiator: Action or EH requesting this
    # actors: players involved
    # categories: card categories, eg: ['cards', 'showncards']
    # candidates: players can be selection target, eg: g.players

    assert categories or candidates
    assert actors

    timeout = timeout or 25

    from thb.cards import VirtualCard

    ilet = ActionInputlet(initiator, categories, candidates)

    @ilet.with_post_process
    def process(actor, rst):
        g = Game.getgame()
        usage = getattr(initiator, 'card_usage', 'none')
        try:
            check(rst)
            skills, rawcards, players, params = rst
            [check(not c.detached) for c in rawcards]
            [check(actor.has_skill(s)) for s in skills]  # has_skill may be hooked

            if skills:
                cards = [skill_wrap(actor, skills, rawcards, params)]
                usage = cards[0].usage if usage == 'launch' else usage
            else:
                cards = rawcards
                usage = 'launch'

            if categories:
                if len(cards) == 1 and cards[0].is_card(VirtualCard):
                    def walk(c):
                        if not c.is_card(VirtualCard): return
                        if getattr(c, 'no_reveal', False): return

                        g.players.reveal(c.associated_cards)
                        for c1 in c.associated_cards:
                            walk(c1)

                    walk(cards[0])
                    check(skill_check(cards[0]))

                else:
                    if not getattr(initiator, 'no_reveal', False):
                        g.players.reveal(cards)

                check(initiator.cond(cards))
                assert not (usage == 'none' and rawcards)  # should not pass check
            else:
                cards = []

            if candidates:
                players, valid = initiator.choose_player_target(players)
                check(valid)

            ask_for_action_verify = getattr(initiator, 'ask_for_action_verify', None)

            if ask_for_action_verify:
                check(ask_for_action_verify(actor, cards, players))

            return cards, players, params

        except CheckFailed:
            return None

    p, rst = user_input(actors, ilet, timeout=timeout, type='any', trans=trans)
    if rst:
        cards, players, params = rst

        if len(cards) == 1 and cards[0].is_card(VirtualCard):
            Game.getgame().deck.register_vcard(cards[0])

        if not cards and not players:
            return p, None

        [c.detach() for c in VirtualCard.unwrap(cards)]

        return p, (cards, players)
    else:
        return None, None


def user_choose_cards(initiator, actor, categories, timeout=None, trans=None):
    check_type([str, Ellipsis], categories)

    _, rst = ask_for_action(initiator, [actor], categories, (), timeout=timeout, trans=trans)
    if not rst:
        return None

    return rst[0]  # cards


def user_choose_players(initiator, actor, candidates, timeout=None, trans=None):
    _, rst = ask_for_action(initiator, [actor], (), candidates, timeout=timeout, trans=trans)
    if not rst:
        return None

    return rst[1]  # players


def random_choose_card(cardlists):
    from itertools import chain
    allcards = list(chain.from_iterable(cardlists))
    if not allcards:
        return None

    g = Game.getgame()
    c = g.random.choice(allcards)
    v = sync_primitive(c.sync_id, g.players)
    cl = g.deck.lookupcards([v])
    assert len(cl) == 1
    c = cl[0]
    c.detach()
    return c


def skill_wrap(actor, skills, cards, params):
    assert skills
    for skill_cls in skills:
        card = skill_cls.wrap(cards, actor, params)
        cards = [card]

    return cards[0]


def skill_check(wrapped):
    from thb.cards.base import Skill

    try:
        check(wrapped.check())
        for c in wrapped.associated_cards:
            if c.is_card(Skill):
                check(c.player is wrapped.player)
                check(skill_check(c))
            else:
                check(c.resides_in.owner is wrapped.player)

        return True

    except CheckFailed:
        return False


class MigrateCardsTransaction(object):
    def __init__(self, action):
        self.action = action
        self.cancelled = False
        self.movements = []

    def move(self, cards, _from, to, is_bh, front):
        self.movements.append((cards, _from, to, is_bh, front))

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        if not self.cancelled:
            self.commit()
        else:
            log.debug('migrate_cards cancelled: %s', self.movements)

    def commit(self):
        g = Game.getgame()
        DETACHED = migrate_cards.DETACHED
        UNWRAPPED = migrate_cards.UNWRAPPED
        from thb.cards import VirtualCard
        act = self.action

        for cards, _from, to, is_bh, front in self.movements:
            if to is DETACHED:
                for c in cards: c.detach()

            elif to is UNWRAPPED:
                for c in cards:
                    assert c.is_card(VirtualCard) and not c.unwrapped
                    c.detach()
                    c.unwrapped = True

            else:
                for c in cards:
                    c.move_to(to)

                if front:
                    to.rotate(len(cards))

        for cards, _from, to, is_bh, front in self.movements:
            g.emit_event('card_migration', (act, cards, _from, to, is_bh))

        g.emit_event('post_card_migration', self)

    def get_movements(self, include_detach=False, only_detach=False):
        assert not (include_detach and only_detach)

        if include_detach:
            return self.movements
        elif only_detach:
            return (m for m in self.movements if m[2] is migrate_cards.DETACHED)
        else:
            return (m for m in self.movements if m[2] is not migrate_cards.DETACHED)


def migrate_cards(cards, to, unwrap=False, is_bh=False, front=False, trans=None):
    '''
    cards: cards to move around
    to: destination card list
    unwrap: drop all VirtualCard wrapping, preserve PhysicalCard only
    is_bh: indicates this operation is bottom half of a complete migration (pairing with detach_cards)
    front: Rotate migrated cards to front (if not, cards are appended to the back of CardList)
    trans: associated MigrateCardsTransaction
    '''
    if not trans:
        with MigrateCardsTransaction(Game.getgame().action_stack[-1]) as trans:
            migrate_cards(cards, to, unwrap, is_bh, front, trans)
            return not trans.cancelled

    if to.owner and to.owner.dead:
        # do not migrate cards to dead character
        trans.cancelled = True
        return

    from .cards import VirtualCard
    groups = group_by(cards, lambda c: id(c) if c.is_card(VirtualCard) else id(c.resides_in))

    DETACHED = migrate_cards.DETACHED
    UNWRAPPED = migrate_cards.UNWRAPPED
    detaching = to is DETACHED

    for l in groups:
        cl = l[0].resides_in

        if l[0].is_card(VirtualCard):
            assert len(l) == 1
            trans.move(l, cl, UNWRAPPED if unwrap else to, False, is_bh)
            l[0].unwrapped or migrate_cards(
                l[0].associated_cards,
                to if unwrap or detaching else to.owner.special,
                unwrap if type(unwrap) is bool else unwrap - 1,
                is_bh,
                front,
                trans
            )

        else:
            trans.move(l, cl, to, is_bh, front)


class PostCardMigrationHandler(EventHandlerGroup):
    interested = ('post_card_migration',)

    def handle(self, evt_type, arg):
        if evt_type != 'post_card_migration': return arg

        g = Game.getgame()
        act = arg.action
        tgt = act.target or act.source or g.players[0]

        for p in g.players_from(tgt):
            for eh in self.handlers:
                g.handle_single_event(eh, p, arg)

        return arg


def detach_cards(cards, trans=None):
    migrate_cards(cards, migrate_cards.DETACHED, trans=trans)


class _MigrateCardsDetached(object):
    owner = None
    type = 'detached'

    def __repr__(self):
        return 'DETACHED'


class _MigrateCardsUnwrapped(object):
    owner = None
    type = 'unwrapped'

    def __repr__(self):
        return 'UNWRAPPED'


migrate_cards.SINGLE_LAYER = 1
migrate_cards.DETACHED = _MigrateCardsDetached()
migrate_cards.UNWRAPPED = _MigrateCardsUnwrapped()


def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls


action_eventhandlers = set()

# ------------------------------------------


class GenericAction(Action):
    pass


class UserAction(Action):  # card/character skill actions
    pass


class DeadDropCards(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()

        others = g.players.exclude(tgt)
        from .actions import DropCards
        lists = [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell, tgt.special]
        lists.extend(tgt.showncardlists)
        for cl in lists:
            if not cl: continue
            others.reveal(list(cl))
            g.process_action(DropCards(tgt, tgt, cl))
            assert not cl

        return True


class PlayerDeath(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.dead = True
        tgt.skills[:] = []
        tgt.tags.clear()
        g = Game.getgame()
        g.process_action(DeadDropCards(tgt, tgt))
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
        self.revived_by = None
        if target.dead:
            log.error('TryRevive buggy condition, __init__')
            return

    def apply_action(self):
        tgt = self.target

        if tgt.dead:
            log.error('TryRevive buggy condition, apply')
            import traceback
            traceback.print_stack()
            return False

        g = Game.getgame()
        from .cards import AskForHeal
        for p in g.players_from(tgt):
            while True:
                if p.dead:
                    break

                if g.process_action(AskForHeal(tgt, p)):
                    if tgt.life > 0:
                        self.revived_by = p
                        return True
                    continue

                break

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
        tgt.life -= max(self.amount, 0)
        return True

    def is_valid(self):
        return not self.target.dead


class Damage(BaseDamage):
    pass


class LifeLost(BaseDamage):
    def __init__(self, source, target, amount=1):
        self.source = None
        self.target = target
        self.amount = amount


class MaxLifeChange(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()
        tgt.maxlife += self.amount

        if tgt.life > tgt.maxlife:
            g.process_action(
                LifeLost(src, tgt, abs(tgt.life - tgt.maxlife))
            )
            assert tgt.life == tgt.maxlife

        assert tgt.maxlife or tgt.dead

        return True

    def is_valid(self):
        return not self.target.dead


# ---------------------------------------------------

class DropCards(GenericAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = self.cards
        assert all(c.resides_in.owner in (target, None) for c in cards), 'WTF?!'
        migrate_cards(cards, g.deck.droppedcards, unwrap=True)

        return True

    def is_valid(self):
        return True


class UseCard(GenericAction):

    def __init__(self, target, card):
        self.source = self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        c = self.card
        act = getattr(c, 'use_action', None)
        if act:
            return g.process_action(act(tgt, c))
        else:
            migrate_cards([c], g.deck.droppedcards, unwrap=True)
            return True

    def can_fire(self):
        c = self.card
        act = getattr(c, 'use_action', None)
        if act:
            return act(self.target, self.card).can_fire()
        else:
            try:
                _ = Game.getgame().emit_event('action_shootdown', self)
                assert _ is self, "You can't replace action in 'action_shootdown' event!"
            except ActionShootdown as e:
                return e
            return True


class AskForCard(GenericAction):

    def __init__(self, source, target, card_cls, categories=('cards', 'showncards')):
        self.source = source
        self.target = target
        self.card_cls = card_cls
        self.categories = categories
        self.card = None

    def apply_action(self):
        target = self.target

        if not self.card:  # ask if not already provided
            cards = user_choose_cards(self, target, self.categories)
            if not cards or len(cards) != 1:
                self.card = None
                return False

            self.card = cards[0]

        return self.process_card(self.card)

    def cond(self, cl):
        from thb import cards
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(self.card_cls) and
            (cl[0].is_card(cards.VirtualCard) or cl[0].resides_in.owner is t)
        )

    def process_card(self, card):
        raise NotImplementedError


class ActiveDropCards(GenericAction):
    card_usage = 'drop'

    def __init__(self, source, target, dropn):
        self.source = source
        self.target = target
        self.dropn = dropn
        self.cards = []

    def apply_action(self):
        tgt = self.target
        if tgt.dead: return False
        n = self.dropn
        if n <= 0: return True

        g = Game.getgame()
        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        if cards:
            g.process_action(DropCards(tgt, tgt, cards=cards))
        else:
            from itertools import chain
            cards = list(chain(tgt.cards, tgt.showncards))[min(-n, 0):]
            g.players.reveal(cards)
            g.process_action(DropCards(tgt, tgt, cards=cards))

        self.cards = cards
        return True

    def cond(self, cards):
        tgt = self.target
        if not len(cards) == self.dropn:
            return False

        if not all(c.resides_in in (tgt.cards, tgt.showncards) for c in cards):
            return False

        from .cards import Skill
        if any(c.is_card(Skill) for c in cards):
            return False

        return True


class DropCardStage(ActiveDropCards):
    def __init__(self, target):
        dropn = len(target.cards) + len(target.showncards) - target.life
        ActiveDropCards.__init__(self, target, target, dropn)


class BaseDrawCards(GenericAction):
    def __init__(self, target, amount=2, back=False):
        self.source = self.target = target
        self.amount = amount
        self.back = back

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        if self.back:
            g.deck.getcards(self.amount)  # forcing dropped cards to join if cards in deck are insufficient
            g.deck.cards.rotate(self.amount)

        cards = g.deck.getcards(self.amount)

        target.reveal(cards)
        migrate_cards(cards, target.cards)
        self.cards = cards
        return True

    def is_valid(self):
        return not self.target.dead


class DrawCards(BaseDrawCards):
    pass


class DistributeCards(BaseDrawCards):
    pass


class DrawCardStage(DrawCards):
    pass


class PutBack(GenericAction):
    def __init__(self, source, cards, front=True):
        self.source = self.target = source
        self.cards = cards
        self.front = front

    def apply_action(self):
        g = Game.getgame()
        cards = self.cards

        migrate_cards(cards, g.deck.cards, front=self.front)

        return True


class LaunchCard(GenericAction):
    def __init__(self, source, target_list, card, action=None, bypass_check=False):
        self.force_action = action
        bypass_check = bool(action) or bypass_check
        self.bypass_check = bypass_check
        if bypass_check:
            tl, tl_valid = target_list, True
        else:
            tl, tl_valid = card.target(Game.getgame(), source, target_list)

        self.source, self.target_list, self.card, self.tl_valid = source, tl, card, tl_valid
        self.target = target_list[0] if target_list else source

    def apply_action(self):
        card = self.card
        target_list = self.target_list
        if not card: return False

        action = self.force_action or card.associated_action
        if not action: return False

        g = Game.getgame()
        src = self.source
        card = self.card
        drop = card.usage == 'drop'
        try:
            if drop:  # should drop before action
                g.process_action(DropCards(src, src, cards=[card]))

            elif not getattr(card, 'no_drop', False):
                detach_cards([card])  # emit events

            else:
                card.detach()

            _, tl = g.emit_event('choose_target', (self, target_list))
            assert _ is self

            if not tl:
                return True

            if isinstance(action, Action):
                a = action
            else:
                assert issubclass(action, UserAction)

                tgt = tl[0] if tl else src
                a = action(source=src, target=tgt)
                a.target_list = tl

            a.associated_card = card
            self.card_action = a

            _ = g.emit_event('post_choose_target', (self, tl))
            assert _ == (self, tl)

            g.process_action(a)

            return True
        finally:

            if not drop and card.detached:
                # card/skill still in disputed state,
                # means no actions have done anything to the card/skill,
                # drop it
                if not getattr(card, 'no_drop', False) and not card.unwrapped:
                    migrate_cards([card], g.deck.droppedcards, unwrap=True, is_bh=True)

                else:
                    from .cards import VirtualCard
                    for c in VirtualCard.unwrap([card]):
                        if c.detached: c.attach()

        return True

    def is_valid(self):
        if self.bypass_check:
            return True

        if not self.tl_valid:
            log.debug('LaunchCard.tl_valid FALSE')
            return False

        card = self.card
        if not card:
            log.debug('LaunchCard.card FALSE')
            return False

        src = self.source

        dist = self.calc_distance(src, card)
        if not all([dist[p] <= 0 for p in self.target_list]):
            log.debug('LaunchCard: does not fulfill distance constraint')
            return False

        cls = card.associated_action

        tl = self.target_list
        target = tl[0] if tl else src
        act = cls(source=src, target=target)
        act.associated_card = card
        act.target_list = tl
        try:
            act.action_shootdown_exception()
        except:
            log.debug('LaunchCard card_action.can_fire() FALSE')
            raise

        return True

    @classmethod
    def calc_distance(cls, source, card):
        dist = cls.calc_base_distance(source)
        g = Game.getgame()

        g.emit_event('calcdistance', (source, card, dist))
        card_dist = getattr(card, 'distance', 1000)
        for p in dist:
            dist[p] -= card_dist
        g.emit_event('post_calcdistance', (source, card, dist))

        return dist

    @classmethod
    def calc_raw_distance(cls, source, card):
        dist = cls.calc_base_distance(source)
        g = Game.getgame()

        g.emit_event('calcdistance', (source, card, dist))
        return dist

    @classmethod
    def calc_base_distance(cls, src):
        g = Game.getgame()
        pl = [p for p in g.players if not p.dead or p is src]
        loc = pl.index(src)
        n = len(pl)
        dist = OrderedDict([
            (p, min(abs(i), n - abs(i)))
            for p, i in zip(pl, xrange(-loc, -loc + n))
        ])
        return dist


class ActionStageLaunchCard(LaunchCard):
    pass


class BaseActionStage(GenericAction):
    card_usage = 'launch'

    def __init__(self, target):
        self.source = self.source = target
        self.target = target
        self.in_user_input = False
        self._force_break = False
        self.action_count = 0

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if target.dead: return False

        try:
            while not target.dead:
                try:
                    g.emit_event('action_stage_action', target)
                    self.in_user_input = True
                    with InputTransaction('ActionStageAction', [target]) as trans:
                        p, rst = ask_for_action(
                            self, [target], ('cards', 'showncards'), g.players, trans=trans
                        )
                    check(p is target)
                finally:
                    self.in_user_input = False

                cards, target_list = rst
                g.players.reveal(cards)
                card = cards[0]

                lc = self.launch_card_cls(target, target_list, card)
                if not g.process_action(lc):
                    if lc.invalid:
                        log.debug('ActionStage: LaunchCard invalid.')
                        check(False)

                self.action_count += 1

                if self.one_shot or self._force_break:
                    break

        except CheckFailed:
            pass

        return True

    @staticmethod
    def force_break():
        g = Game.getgame()
        for a in g.action_stack:
            if isinstance(a, ActionStage):
                a._force_break = True
                log.debug('ActioStage: force_break requested')
                break

    def cond(self, cl):
        from .cards import Skill
        if not cl: return False

        tgt = self.target
        if not len(cl) == 1:
            return False

        c = cl[0]
        return (
            c.is_card(Skill) or c.resides_in in (tgt.cards, tgt.showncards)
        ) and bool(c.associated_action)

    def ask_for_action_verify(self, p, cl, tl):
        assert len(cl) == 1
        return self.launch_card_cls(p, tl, cl[0]).can_fire()

    def choose_player_target(self, tl):
        return tl, True


class ActionStage(BaseActionStage):
    one_shot = False
    launch_card_cls = ActionStageLaunchCard


@register_eh
class ShuffleHandler(EventHandler):
    interested = ('action_after', 'action_before', 'action_stage_action', 'card_migration', 'user_input_start')

    def handle(self, evt_type, arg):
        if evt_type == 'action_stage_action':
            self.do_shuffle()

        elif evt_type in ('action_before', 'action_after') and isinstance(arg, ActionStage):
            self.do_shuffle()

        elif evt_type == 'user_input_start':
            trans, ilet = arg
            if isinstance(ilet, ChoosePeerCardInputlet):
                self.do_shuffle([ilet.target])

        # <!-- This causes severe problems, do not use -->
        # elif evt_type == 'card_migration':
        #     act, cl, _from, to, _ = arg
        #     to.owner and to.type == 'cards' and self.do_shuffle([to.owner])

        return arg

    @staticmethod
    def do_shuffle(pl=None):
        from .cards import VirtualCard
        g = Game.getgame()

        for p in pl or g.players:
            if not p.cards: continue
            if any([c.is_card(VirtualCard) for c in p.cards]):
                log.warning('VirtualCard in cards of %s, not shuffling.' % repr(p))
                continue

            g.deck.shuffle(p.cards)


class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if target.dead: return False
        ft_cards = target.fatetell
        while ft_cards:
            if target.dead: break
            card = ft_cards[-1]  # what comes last, launches first.
            g.process_action(LaunchFatetellCard(target, card))

        return True


class BaseFatetell(GenericAction):
    def __init__(self, target, cond):
        self.target = target
        self.cond = cond
        self.initiator = Game.getgame().hybrid_stack[-1]
        self.card_manipulator = self

    def apply_action(self):
        g = Game.getgame()
        card, = g.deck.getcards(1)
        g.players.reveal(card)
        self.card = card
        detach_cards([card])
        g.emit_event(self.type, self)
        return self.succeeded

    def set_card(self, card, card_manipulator):
        self.card = card
        self.card_manipulator = card_manipulator

    @property
    def succeeded(self):
        # This is necessary, for ui
        return self.cond(self.card)


class Fatetell(BaseFatetell):
    type = 'fatetell'


class TurnOverCard(BaseFatetell):
    type = 'turnover'


class FatetellMalleateHandler(EventHandlerGroup):
    interested = ('fatetell',)

    def handle(self, evt_type, data):
        if evt_type != 'fatetell': return data

        g = Game.getgame()
        for p in g.players_from(g.current_player):
            for eh in self.handlers:
                data = g.handle_single_event(eh, p, data)

        return data


class FatetellAction(GenericAction):
    fatetell_target = None

    def apply_action(self):
        assert self.fatetell_target is not None, 'Should specify fatetell_target!'

        ft = Fatetell(self.fatetell_target, self.fatetell_cond)
        g = Game.getgame()
        g.process_action(ft)

        if not ft.cancelled:
            rst = self.fatetell_action(ft)

            assert ft.card
            if ft.card.detached:
                with MigrateCardsTransaction(ft.card_manipulator) as trans:
                    migrate_cards([ft.card], g.deck.droppedcards, unwrap=True, is_bh=True, trans=trans)

            return rst

        return False

    def fatetell_action(self, ft):
        raise Exception('Implement fatetell_action!')

    def fatetell_cond(self, card):
        raise Exception('Implement fatetell_cond!')

    def fatetell_postprocess(self):
        pass


class LaunchFatetellCard(GenericAction):
    def __init__(self, target, card):
        self.source = None
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        card = self.card
        act = card.delayed_action
        assert act
        a = act(source=target, target=target)
        a.associated_card = card
        self.card_action = a
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

        try:
            self.prepare()
            for t in tl:
                if t.dead and not self.include_dead:
                    continue
                a = self.action_cls(source, t)
                a.associated_card = card
                a.parent_action = self
                g.process_action(a)

        finally:
            self.cleanup()

        return True

    @classmethod
    def get_actual_action(self, act):
        assert isinstance(act, Action)
        return getattr(act, 'parent_action', None)

    @classmethod
    def is_group_effect(self, act):
        return getattr(self.get_actual_action(act), 'group_effect', False)


class PrepareStage(GenericAction):
    def __init__(self, target):
        self.source = target
        self.target = target

    def apply_action(self):
        return True


class FinalizeStage(GenericAction):
    def __init__(self, target):
        self.source = target
        self.target = target

    def apply_action(self):
        return True


class PlayerTurn(GenericAction):
    def __init__(self, target):
        self.source = self.target = target
        self.pending_stages = [
            PrepareStage,
            FatetellStage,
            DrawCardStage,
            ActionStage,
            DropCardStage,
            FinalizeStage,
        ]

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        p.tags['turn_count'] += 1
        g.turn_count += 1
        g.current_turn = self
        g.current_player = p

        try:
            while self.pending_stages:
                stage = self.pending_stages.pop(0)
                self.current_stage = cs = stage(p)
                g.process_action(cs)

        finally:
            g.current_turn = None

        return True

    @staticmethod
    def get_current(p=None):
        g = Game.getgame()
        act = getattr(g, 'current_turn', None)
        if act:
            assert isinstance(act, PlayerTurn)

            if p is not None and act.target is not p:
                raise GameException('Got unexpected PlayerTurn!')

        return act


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

    def can_be_seen_by(self, ch):
        if isinstance(self.to, (tuple, list)):
            return ch in self.to
        else:
            return ch is self.to

    def __repr__(self):
        return u'Reveal(%s, %s)' % (self.target, self.to)


class Pindian(UserAction):
    no_reveal = True
    card_usage = 'pindian'

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        pl = BatchList([tgt, src])
        pindian_card = {src: None, tgt: None}

        with InputTransaction('Pindian', pl) as trans:
            for p in pl:
                cards = user_choose_cards(self, p, ('cards', 'showncards'), trans=trans)
                if cards:
                    card = cards[0]
                else:
                    card = random_choose_card([p.cards, p.showncards])

                pindian_card[p] = card
                detach_cards([card])
                g.emit_event('pindian_card_chosen', (p, card))

        g.players.reveal([pindian_card[src], pindian_card[tgt]])
        g.emit_event('pindian_card_revealed', self)  # for ui.
        migrate_cards([pindian_card[src], pindian_card[tgt]], g.deck.droppedcards, unwrap=True, is_bh=True)

        return pindian_card[src].number > pindian_card[tgt].number

    @staticmethod
    def cond(cl):
        from .cards import Skill
        return len(cl) == 1 and \
            (not cl[0].is_card(Skill)) and \
            cl[0].resides_in.type in ('cards', 'showncards')

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.dead or tgt.dead: return False
        if not (src.cards or src.showncards): return False
        if not (tgt.cards or tgt.showncards): return False
        return True


class Reforge(GenericAction):
    card_usage = 'reforge'

    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        migrate_cards([self.card], g.deck.droppedcards, True)
        g.process_action(DrawCards(self.source, 1))

        return True

    def is_valid(self):
        return DrawCards(self.source, 1).can_fire()


@register_eh
class DyingHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseDamage): return act

        src = act.source
        tgt = act.target
        if tgt.dead or tgt.life > 0: return act
        if tgt.tags['in_tryrevive']:
            # nested TryRevive, just return
            # will trigger when Eirin uses Diamond Exinwan to heal self
            return act

        try:
            tgt.tags['in_tryrevive'] = True
            g = Game.getgame()
            if g.process_action(TryRevive(tgt, dmgact=act)):
                return act
        finally:
            tgt.tags['in_tryrevive'] = False

        g.process_action(PlayerDeath(src, tgt))

        return act


class ShowCards(GenericAction):
    def __init__(self, source, cards, to=None):
        self.source = self.target = source
        self.cards = cards
        self.to = to and BatchList(to)

    def apply_action(self):
        if not self.cards:
            return False

        g = Game.getgame()
        cards = self.cards
        to = self.to or g.players
        to.reveal(cards)
        g.emit_event('showcards', (self.target, [copy(c) for c in cards], to))
        # user_input(
        #     [p for p in g.players if not p.dead],
        #     ChooseOptionInputlet(self, (True,)),
        #     type='all', timeout=1,
        # )  # just a delay
        return True


class ActionLimitExceeded(ActionShootdown):
    pass


class VitalityLimitExceeded(ActionLimitExceeded):
    pass
