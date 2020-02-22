# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from copy import copy
from typing import Any, Dict, List, Optional, Sequence, Set, TYPE_CHECKING, Tuple, Type, Union, cast
import logging

# -- third party --
from typing_extensions import Protocol

# -- own --
from game.base import Action, ActionShootdown, EventArbiter, GameViralContext, InputTransaction, GameError
from game.base import Player, sync_primitive
from thb.cards.base import Card, CardList, PhysicalCard, Skill, VirtualCard
from thb.inputlets import ActionInputlet, ChoosePeerCardInputlet
from thb.mode import THBAction, THBEventHandler, THBPlayerAction, THBattle
from thb.common import PlayerRole
from utils.check import CheckFailed, check, check_type
from utils.misc import BatchList, group_by


# -- typing --
if TYPE_CHECKING:
    from thb.characters.base import Character  # noqa: F401

# -- code --
log = logging.getLogger('THBattle_Actions')


# ------------------------------------------
# aux functions

def ttags(actor):
    tags = actor.tags
    tc = tags['turn_count']
    return tags.setdefault('turn_tags:%s' % tc, defaultdict(int))


class CardChooser(Protocol):
    game: THBattle
    card_usage: str

    def cond(self, cards: Sequence[Card]) -> bool: ...


class CharacterChooser(Protocol):
    game: THBattle

    def choose_player_target(self, pl: Sequence[Character]) -> Tuple[List[Character], bool]: ...


def ask_for_action(initiator: Union[CardChooser, CharacterChooser],
                   actors: List[Character],
                   categories: Sequence[str],
                   candidates: Sequence[Character],
                   timeout: Optional[int] = None,
                   trans: Optional[InputTransaction] = None,
                   ) -> Tuple[Optional[Character], Optional[Tuple[List[Card], List[Character]]]]:
    # initiator: Action or EH requesting this
    # actors: players involved
    # categories: card categories, eg: ['cards', 'showncards']
    # candidates: players can be selection target, eg: g.players

    assert categories or candidates
    assert actors

    timeout = timeout or 25

    from thb.cards.base import VirtualCard

    g = cast(THBattle, initiator.game)

    ilet = ActionInputlet(initiator, categories, candidates)

    @ilet.with_post_process
    def process(actor: Character, rst):
        usage = getattr(initiator, 'card_usage', 'none')
        try:
            check(rst)

            skills: List[Type[Skill]]
            rawcards: List[Card]
            characters: List[Character]
            params: Dict[str, Any]

            skills, rawcards, characters, params = rst
            [check(not c.detached) for c in rawcards]
            [check(actor.has_skill(s)) for s in skills]  # has_skill may be hooked

            if skills:
                cards = [skill_wrap(actor, skills, rawcards, params)]
                usage = cards[0].usage if usage == 'launch' else usage
                assert usage != 'none', (cards[0], cards[0].usage)
            else:
                cards = rawcards
                usage = 'launch'

            if categories:
                if len(cards) == 1 and cards[0].is_card(VirtualCard):
                    def walk(c: Card):
                        if not c.is_card(VirtualCard): return
                        if getattr(c, 'no_reveal', False): return

                        c = cast(VirtualCard, c)

                        g.players.player.reveal(c.associated_cards)
                        for c1 in c.associated_cards:
                            walk(c1)

                    walk(cards[0])
                    check(skill_check(cards[0]))

                else:
                    if not getattr(initiator, 'no_reveal', False):
                        g.players.player.reveal(cards)

                check(cast(CardChooser, initiator).cond(cards))
                assert not (usage == 'none' and rawcards), (skills, rawcards, characters, params)  # should not pass check
            else:
                cards = []

            if candidates:
                characters, valid = cast(CharacterChooser, initiator).choose_player_target(characters)
                check(valid)

            ask_for_action_verify = getattr(initiator, 'ask_for_action_verify', None)

            if ask_for_action_verify:
                check(ask_for_action_verify(actor, cards, characters))

            return cards, characters, params

        except CheckFailed:
            return None

    p, rst = g.user_input(actors, ilet, timeout=timeout, type='any', trans=trans)
    if rst:
        cards, characters, params = rst

        if len(cards) == 1 and cards[0].is_card(VirtualCard):
            g.deck.register_vcard(cards[0])

        if not cards and not characters:
            return p, None

        [c.detach() for c in VirtualCard.unwrap(cards)]

        return p, (cards, characters)
    else:
        return None, None


def user_choose_cards(initiator: CardChooser,
                      actor: Character,
                      categories: Sequence[str],
                      timeout: Optional[int] = None,
                      trans: Optional[InputTransaction] = None,
                      ) -> Optional[List[Card]]:
    check_type([str, ...], categories)

    _, rst = ask_for_action(initiator, [actor], categories, (), timeout=timeout, trans=trans)
    if not rst:
        return None

    return rst[0]  # cards


def user_choose_players(initiator: CharacterChooser,
                        actor: Character,
                        candidates: List[Character],
                        timeout: Optional[int] = None,
                        trans: Optional[InputTransaction] = None,
                        ) -> Optional[List[Character]]:
    _, rst = ask_for_action(initiator, [actor], (), candidates, timeout=timeout, trans=trans)
    if not rst:
        return None

    return rst[1]  # players


def random_choose_card(g: THBattle, cardlists: Sequence[Sequence]):
    from itertools import chain
    allcards = list(chain.from_iterable(cardlists))
    if not allcards:
        return None

    c = g.random.choice(allcards)
    v = sync_primitive(c.sync_id, g.players.player)
    c = g.deck.lookup(v)
    assert c
    c.detach()
    return c


def skill_wrap(actor: Character, skills: List[Type[Skill]], cards: List[Card], params: Dict[str, Any]):
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
                check(c.character is wrapped.character)
                check(skill_check(c))
            else:
                check(c.resides_in.owner is wrapped.character)

        return True

    except CheckFailed:
        return False


COMMON_EVENT_HANDLERS: Set[Type[THBEventHandler]] = set()


def register_eh(cls):
    COMMON_EVENT_HANDLERS.add(cls)
    return cls


# ------------------------------------------
class GenericAction(THBAction):
    pass


class UserAction(THBAction):  # card/character skill actions
    target_list: Sequence[Character]
    associated_card: Card


CardMovement = Tuple[List[Card], Optional[CardList], Optional[CardList], bool]


class MigrateCardsTransaction(GameViralContext):
    movements: List[CardMovement]

    def __init__(self, action: Optional[THBAction] = None):
        g = self.game
        self.action = cast(THBAction, action or g.action_stack[-1])

        if self.action is g.action_stack[-1]:
            # Ensure no card movements in EventHandlers!
            assert self.action is g.hybrid_stack[-1], (self.action, g.hybrid_stack[-1])

        self.cancelled = False
        self.movements = []

    def move(self, cards: List[Card], _from: Optional[CardList], to: Optional[CardList], is_bh: bool) -> None:
        self.movements.append((cards, _from, to, is_bh))

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        if not self.cancelled:
            self.commit()
        else:
            log.debug('migrate_cards cancelled: %s', self.movements)

    def commit(self):
        g = self.game
        DETACHED = MigrateSpecial.DETACHED
        UNWRAPPED = MigrateSpecial.UNWRAPPED
        act = self.action

        for cards, _from, to, is_bh in self.movements:
            if to is DETACHED:
                for c in cards: c.detach()

            elif to is UNWRAPPED:
                for c in cards:
                    assert c.is_card(VirtualCard) and not c.unwrapped
                    c.detach()
                    c.unwrapped = True

            else:
                for c in cards: c.move_to(to)

        for cards, _from, to, is_bh in self.movements:
            g.emit_event('card_migration', (act, cards, _from, to, is_bh))

        g.emit_event('post_card_migration', self)

    def get_movements(self, include_detach=False, only_detach=False):
        assert not (include_detach and only_detach)

        if include_detach:
            return self.movements
        elif only_detach:
            return (m for m in self.movements if m[2] is MigrateSpecial.DETACHED)
        else:
            return (m for m in self.movements if m[2] is not MigrateSpecial.DETACHED)


def migrate_cards(cards: Sequence[Card],
                  to: CardList,
                  unwrap: bool = False,
                  is_bh: bool = False,
                  trans: Optional[MigrateCardsTransaction] = None,
                  ):
    '''
    cards: cards to move around
    to: destination card list
    unwrap: tear down VirtualCard wrapping, preserve PhysicalCard only, at most X layers
    is_bh: indicates this operation is bottom half of a complete migration (pairing with detach_cards)
    trans: associated MigrateCardsTransaction
    '''
    if not trans:
        with MigrateCardsTransaction() as t:
            migrate_cards(cards, to, unwrap, is_bh, t)
            return not t.cancelled

    if to.owner and to.owner.dead:
        # do not migrate cards to dead character
        trans.cancelled = True
        return

    groups = group_by(cards, lambda c: id(c) if c.is_card(VirtualCard) else id(c.resides_in))

    DETACHED = MigrateSpecial.DETACHED
    UNWRAPPED = MigrateSpecial.UNWRAPPED
    detaching = to is DETACHED

    for l in groups:
        cl = l[0].resides_in

        if l[0].is_card(VirtualCard):
            assert len(l) == 1
            # assert to.owner # ??????
            trans.move(l, cl, UNWRAPPED if unwrap else to, is_bh)
            l[0].unwrapped or migrate_cards(
                l[0].associated_cards,
                to if unwrap or detaching else to.owner.special,
                unwrap if isinstance(unwrap, bool) else unwrap - 1,
                is_bh,
                trans
            )

        else:
            trans.move(l, cl, to, is_bh)


class MigrateSpecial(object):
    DETACHED     = CardList(None, 'DETACHED')
    UNWRAPPED    = CardList(None, 'UNWRAPPED')
    SINGLE_LAYER = 1


class PostCardMigrationHandler(EventArbiter):
    interested = ['post_card_migration']

    def handle(self, evt_type, arg):
        if evt_type != 'post_card_migration': return arg

        g = self.game
        act = arg.action
        tgt = act.target or act.source or g.players[0]

        n = len(g.players)
        idx = g.players.index(tgt) - n
        for i in range(idx, idx + n):
            for eh in self.handlers:
                g.dispatcher.handle_single_event(eh, g.players[i], arg)

        return arg


def detach_cards(cards: Sequence[Card], trans=None):
    migrate_cards(cards, MigrateSpecial.DETACHED, trans=trans)


class DeadDropCards(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = self.game

        others = g.players.exclude(tgt)
        lists = [tgt.cards, tgt.showncards, tgt.equips, tgt.fatetell, tgt.special]
        lists.extend(tgt.showncardlists)
        for cl in lists:
            if not cl: continue
            others.reveal(list(cl))
            g.process_action(DropCards(tgt, tgt, cl))
            assert not cl

        return True


class PlayerDeath(GenericAction):
    # FIXME: should be `CharacterDeath`
    def apply_action(self) -> bool:
        tgt = self.target
        tgt.dead = True
        g = self.game
        g.process_action(DeadDropCards(tgt, tgt))
        tgt.skills[:] = []  # FIXME: should be here now?
        tgt.tags.clear()
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
    def __init__(self, target: Character, dmgact: BaseDamage):
        self.source = self.target = target
        self.dmgact = dmgact
        self.revived_by: Optional[Character] = None
        if target.dead:
            log.error('TryRevive buggy condition, __init__')
            return

    def apply_action(self) -> bool:
        tgt = self.target

        if tgt.dead:
            log.error('TryRevive buggy condition, apply')
            import traceback
            traceback.print_stack()
            return False

        g = self.game
        from thb.cards.basic import AskForHeal
        for p in g.players.rotate_to(tgt):
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
        tgt.life -= self.amount
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
        g = self.game
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
        g = self.game
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
        g = self.game
        migrate_cards([self.card], g.deck.droppedcards, unwrap=True)

        return True


class AskForCard(GenericAction):

    def __init__(self, source: Character, target: Character, card_cls: Type[PhysicalCard], categories: Sequence[str]=('cards', 'showncards')):
        self.source = source
        self.target = target
        self.card_cls = card_cls
        self.categories = categories

        self.card: Optional[Card] = None

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
        from thb.cards.base import VirtualCard
        t = self.target
        return (
            len(cl) == 1 and
            cl[0].is_card(self.card_cls) and
            (cl[0].is_card(VirtualCard) or cl[0].resides_in.owner is t)
        )

    def process_card(self, card):
        raise NotImplementedError


class ActiveDropCards(GenericAction):
    card_usage = 'drop'

    def __init__(self, source: Character, target: Character, dropn: int) -> None:
        self.source = source
        self.target = target
        self.dropn = dropn
        self.cards: List[Card] = []

    def apply_action(self) -> bool:
        tgt = self.target
        if tgt.dead: return False
        n = self.dropn
        if n <= 0: return True

        g = self.game
        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        if cards:
            g.process_action(DropCards(tgt, tgt, cards=cards))
        else:
            from itertools import chain
            cards = list(chain(tgt.cards, tgt.showncards))[min(-n, 0):]
            g.players.player.reveal(cards)
            g.process_action(DropCards(tgt, tgt, cards=cards))

        self.cards = cards
        return True

    def cond(self, cards: Sequence[Card]) -> bool:
        tgt = self.target
        if not len(cards) == self.dropn:
            return False

        if not all(c.resides_in in (tgt.cards, tgt.showncards) for c in cards):
            return False

        from thb.cards.base import Skill
        if any(c.is_card(Skill) for c in cards):
            return False

        return True


class DropCardStage(ActiveDropCards):
    def __init__(self, target):
        dropn = len(target.cards) + len(target.showncards) - target.life
        ActiveDropCards.__init__(self, target, target, dropn)


class BaseDrawCards(GenericAction):
    def __init__(self, target, amount=2):
        self.source = self.target = target
        self.amount = amount

    def apply_action(self):
        g = self.game
        target = self.target

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


class LaunchCard(GenericAction):
    def __init__(self, src: Character,
                       target_list: Sequence[Character],
                       card: Card,
                       action: Optional[UserAction] = None,
                       bypass_check=False):
        self.force_action = action
        bypass_check = bool(action) or bypass_check
        self.bypass_check = bypass_check
        if bypass_check:
            tl, tl_valid = target_list, True
        else:
            tl, tl_valid = card.target(self.game, src, target_list)

        self.source, self.target_list, self.card, self.tl_valid = src, tl, card, tl_valid
        self.target = target_list[0] if target_list else src

    def apply_action(self) -> bool:
        card = self.card
        target_list = self.target_list
        if not card: return False

        if not self.force_action and not card.associated_action:
            return False

        g = self.game
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

            if self.force_action:
                a = self.force_action
            else:
                tgt = tl[0] if tl else src
                assert card.associated_action
                a = card.associated_action(source=src, target=tgt)
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
                    from thb.cards.base import VirtualCard
                    for c in VirtualCard.unwrap([card]):
                        if c.detached: c.attach()

        return True

    def is_valid(self) -> bool:
        if self.bypass_check:
            return True

        if not self.tl_valid:
            log.debug('LaunchCard.tl_valid FALSE')
            return False

        card = self.card
        if not card:
            log.debug('LaunchCard.card FALSE')
            return False

        g = self.game
        src = self.source

        dist = self.calc_distance(g, src, card)
        if not all([dist[p] <= 0 for p in self.target_list]):
            log.debug('LaunchCard: does not fulfill distance constraint')
            return False

        cls = card.associated_action
        if not cls:
            return False

        tl = self.target_list
        target = tl[0] if tl else src
        act = cls(source=src, target=target)
        act.associated_card = card
        act.target_list = tl
        try:
            act.action_shootdown_exception()
        except Exception:
            log.debug('LaunchCard card_action.can_fire() FALSE')
            raise

        return True

    @classmethod
    def calc_distance(cls, g, src, card):
        dist = cls.calc_raw_distance(g, src, card)
        card_dist = getattr(card, 'distance', 1000)
        for p in dist:
            dist[p] -= card_dist
        g.emit_event('post_calcdistance', (src, card, dist))
        return dist

    @classmethod
    def calc_raw_distance(cls, g, src, card):
        dist = cls.calc_base_distance(g, src)
        g.emit_event('calcdistance', (src, card, dist))
        return dist

    @classmethod
    def calc_base_distance(cls, g, src):
        pl = [p for p in g.players if not p.dead or p is src]
        loc = pl.index(src)
        n = len(pl)
        dist = {
            p: min(abs(i), n - abs(i))
            for p, i in zip(pl, range(-loc, -loc + n))
        }
        return dist


class ActionStageLaunchCard(LaunchCard):
    pass


class BaseActionStage(GenericAction):
    card_usage = 'launch'
    launch_card_cls: Type[LaunchCard]

    def __init__(self, target):
        self.source = self.source = target
        self.target = target
        self.in_user_input = False
        self._force_break = False
        self.action_count = 0

    def apply_action(self):
        g = self.game
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
                    assert rst
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
    def force_break(g):
        for a in g.action_stack:
            if isinstance(a, ActionStage):
                a._force_break = True
                break

    def cond(self, cl):
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
class ShuffleHandler(THBEventHandler):
    interested = ['action_after', 'action_before', 'action_stage_action', 'card_migration', 'user_input_start']

    def handle(self, evt_type, arg):
        g = self.game
        if evt_type == 'action_stage_action':
            self.do_shuffle(g, g.players)

        elif evt_type in ('action_before', 'action_after') and isinstance(arg, ActionStage):
            self.do_shuffle(g, g.players)

        elif evt_type == 'user_input_start':
            trans, ilet = arg
            if isinstance(ilet, ChoosePeerCardInputlet):
                self.do_shuffle(g, [ilet.target])

        # <!-- This causes severe problems, do not use -->
        # elif evt_type == 'card_migration':
        #     act, cl, _from, to, _ = arg
        #     to.owner and to.type == 'cards' and self.do_shuffle([to.owner])

        return arg

    @staticmethod
    def do_shuffle(g, pl):
        for p in pl:
            if not p.cards: continue
            if any([c.is_card(VirtualCard) for c in p.cards]):
                log.warning('VirtualCard in cards of %s, not shuffling.' % repr(p))
                continue

            g.deck.shuffle(p.cards)


class FatetellStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = self.game
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
        self.initiator = self.game.hybrid_stack[-1]
        self.card_manipulator = self

    def apply_action(self):
        g = self.game
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


class FatetellMalleateHandler(EventArbiter):
    interested = ['fatetell']

    def handle(self, evt_type, data):
        if evt_type != 'fatetell': return data

        g = self.game
        tgt = PlayerTurn.get_current(g).target

        n = len(g.players)
        idx = g.players.index(tgt) - n
        for i in range(idx, idx + n):
            for eh in self.handlers:
                g.dispatcher.handle_single_event(eh, g.players[i], data)

        return data


class FatetellAction(GenericAction):
    fatetell_target = None

    def apply_action(self):
        assert self.fatetell_target is not None, 'Should specify fatetell_target!'

        ft = Fatetell(self.fatetell_target, self.fatetell_cond)
        g = self.game
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
        g = self.game
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
        g = self.game

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
        self.target = target

    def apply_action(self):
        return True


class FinalizeStage(GenericAction):
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        return True


class PlayerTurn(GenericAction):
    def __init__(self, target: Character):
        self.source = self.target = target
        self.pending_stages = [
            PrepareStage,
            FatetellStage,
            DrawCardStage,
            ActionStage,
            DropCardStage,
            FinalizeStage,
        ]

    def apply_action(self) -> bool:
        g = self.game
        p = self.target
        p.tags['turn_count'] += 1

        while self.pending_stages:
            stage = self.pending_stages.pop(0)
            self.current_stage = cs = stage(p)
            g.process_action(cs)

        return True

    @staticmethod
    def get_current(g: THBattle) -> PlayerTurn:
        for act in g.action_stack:
            if isinstance(act, PlayerTurn):
                return act

        raise IndexError('Could not find current turn!')


class DummyAction(GenericAction):
    def __init__(self, source, target, result=True):
        self.source, self.target, self.result = \
            source, target, result

    def apply_action(self):
        return self.result


class RevealRole(THBPlayerAction):

    def __init__(self, role: PlayerRole, to: Union[Player, BatchList[Player]]):
        self.role = role
        self.to = to

    def apply_action(self) -> bool:
        self.to.reveal(self.role)
        return True

    def can_be_seen_by(self, ch: Character) -> bool:
        if isinstance(self.to, BatchList):
            return ch in self.to
        else:
            return ch is self.to


class Pindian(UserAction):
    no_reveal = True
    card_usage = 'pindian'

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self) -> bool:
        src = self.source
        tgt = self.target
        g = self.game

        pl = BatchList([tgt, src])
        pindian_card: Dict[Character, Card] = {}

        with InputTransaction('Pindian', pl) as trans:
            for p in pl:
                cards = user_choose_cards(self, p, ('cards', 'showncards'), trans=trans)
                if cards:
                    card = cards[0]
                else:
                    card = random_choose_card(g, [p.cards, p.showncards])

                pindian_card[p] = card
                detach_cards([card])
                g.emit_event('pindian_card_chosen', (p, card))

        g.players.player.reveal([pindian_card[src], pindian_card[tgt]])
        g.emit_event('pindian_card_revealed', self)  # for ui.
        migrate_cards([pindian_card[src], pindian_card[tgt]], g.deck.droppedcards, unwrap=True, is_bh=True)

        return pindian_card[src].number > pindian_card[tgt].number

    @staticmethod
    def cond(cl):
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
        g = self.game
        migrate_cards([self.card], g.deck.droppedcards, True)
        g.process_action(DrawCards(self.source, 1))

        return True

    def is_valid(self):
        return DrawCards(self.source, 1).can_fire()


@register_eh
class DyingHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseDamage): return act

        src = act.source
        tgt = act.target
        if tgt.dead or tgt.life > 0: return act
        if tgt.tags['in_tryrevive']:
            # nested TryRevive, just return
            # will trigger when Eirin uses Diamond Exinwan to heal herself
            return act

        try:
            tgt.tags['in_tryrevive'] = True
            g = self.game
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

        g = self.game
        cards = self.cards
        to = self.to or g.players
        to.reveal(cards)
        g.emit_event('showcards', (self.target, [copy(c) for c in cards], to))
        # g.user_input(
        #     [p for p in g.players if not p.dead],
        #     ChooseOptionInputlet(self, (True,)),
        #     type='all', timeout=1,
        # )  # just a delay
        return True


class ActionLimitExceeded(ActionShootdown):
    pass


class VitalityLimitExceeded(ActionLimitExceeded):
    pass
