# -*- coding: utf-8 -*-

# All generic and cards' Actions, EventHandlers are here
from game.autoenv import Game, EventHandler, Action
from game.autoenv import sync_primitive, user_input, InputTransaction

from .inputlets import ActionInputlet, ChoosePeerCardInputlet

from utils import check, check_type, CheckFailed, BatchList, group_by

import logging
log = logging.getLogger('THBattle_Actions')

from collections import namedtuple
ActionLimitParams = namedtuple(
    'ActionLimitParams',
    'ilet actor cards players usage'
)


# ------------------------------------------
# aux functions

def ask_for_action(initiator, actors, categories, candidates, trans=None):
    # initiator: Action or EH requesting this
    # actors: players involved
    # categories: card categories, eg: ['cards', 'showncards']
    # candidates: players can be selection target, eg: g.players

    assert categories or candidates
    assert actors

    ilet = ActionInputlet(initiator, categories, candidates)

    @ilet.with_post_process
    def process(actor, rst):
        g = Game.getgame()
        usage = getattr(initiator, 'card_usage', 'none')
        try:
            check(rst)
            skills, cards, players, params = rst
            [check(not c.detached) for c in cards]
            if categories:
                if skills:
                    # check(len(skills) == 1)  # why? disabling it.
                    # will reveal in skill_wrap
                    skill = skill_wrap(actor, skills, cards, params)
                    check(skill)
                    wrapped = [skill]
                    usage = skill.usage if usage == 'launch' else usage
                else:
                    if not getattr(initiator, 'no_reveal', False):
                        g.players.reveal(cards)

                    wrapped = cards

                check(initiator.cond(wrapped))
                assert not (usage == 'none' and cards)  # should not pass check
            else:
                wrapped = []

            if candidates:
                players, valid = initiator.choose_player_target(players)
                check(valid)

            arg = ActionLimitParams(
                ilet=ilet, actor=actor, cards=wrapped,
                players=players, usage=usage
            )
            arg2, permitted = g.emit_event('action_limit', (arg, True))
            assert arg == arg2

            check(permitted)

            return skills, cards, players, params

        except CheckFailed:
            return None

    p, rst = user_input(actors, ilet, type='any', trans=trans)
    if rst:
        skills, cards, players, params = rst
        if skills:
            cards = [skill_transform(p, skills, cards, params)]

        if not cards and not players:
            return p, None

        [c.detach() for c in cards]

        return p, (cards, players)
    else:
        return None, None


def user_choose_cards(initiator, actor, categories, trans=None):
    check_type([str, Ellipsis], categories)

    _, rst = ask_for_action(initiator, [actor], categories, (), trans)
    if not rst:
        return None

    return rst[0]  # cards


def user_choose_players(initiator, actor, candidates, trans=None):
    _, rst = ask_for_action(initiator, [actor], (), candidates, trans)
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
    v = sync_primitive(c.syncid, g.players)
    cl = g.deck.lookupcards([v])
    assert len(cl) == 1
    c = cl[0]
    c.detach()
    return c


def skill_wrap(actor, skills, cards, params, no_reveal=False, detach=False):
    # no_reveal: for ui
    g = Game.getgame()
    try:
        check(all(c.resides_in.owner is actor for c in cards))
        for skill_cls in skills:
            check(skill_cls in actor.skills)

            if not no_reveal and not getattr(skill_cls, 'no_reveal', False):
                g.players.exclude(actor).reveal(cards)

            card = skill_cls.wrap(cards, actor, params)
            check(card.check())

            if detach and not getattr(skill_cls, 'no_drop', False):
                for c in cards: c.detach()

            cards = [card]

        return cards[0]

    except CheckFailed:
        return None


def skill_transform(actor, skills, cards, params):
    g = Game.getgame()
    s = skill_wrap(actor, skills, cards, params, detach=True)
    if not s:
        return None

    g.deck.register_vcard(s)
    # migrate_cards(cards, actor.cards, False, True)
    # s.move_to(actor.cards)
    return s


class MigrateCardsTransaction(object):
    def __init__(self):
        self.action = Game.getgame().action_stack[-1]
        self.movements = []

    def move(self, cards, _from, to):
        self.movements.append((cards, _from, to))

    def __iter__(self):
        return iter(self.movements)

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.commit()

    def commit(self):
        g = Game.getgame()
        DETACHED = migrate_cards.DETACHED
        act = self.action
        
        for cards, _from, to in self.movements:
            if to is not DETACHED:
                for c in cards: c.move_to(to)
            else:
                for c in cards: c.detach()

        for cards, _from, to in self.movements:
            g.emit_event('card_migration', (act, cards, _from, to))

        g.emit_event('post_card_migration', self)


def migrate_cards(cards, to, unwrap=False, detached=False, trans=None):
    if not trans:
        with MigrateCardsTransaction() as trans:
            migrate_cards(cards, to, unwrap, detached, trans)
        return

    g = Game.getgame()
    from .cards import VirtualCard
    groups = group_by(cards, lambda c: id(c) if c.is_card(VirtualCard) else id(c.resides_in))

    DETACHED = migrate_cards.DETACHED
    detaching = to is DETACHED 

    for l in groups:
        if detached:
            assert not [c for c in l if not c.detached]
            cl = DETACHED
        else:
            cl = l[0].resides_in

        if l[0].is_card(VirtualCard):
            assert len(l) == 1
            trans.move(l, cl, DETACHED if unwrap else to)
            migrate_cards(
                l[0].associated_cards,
                to if unwrap or detaching else to.owner.special,
                unwrap if type(unwrap) is bool else unwrap - 1,
                detached,
                trans
            )
        
        else:
            trans.move(l, cl, to)


def detach_cards(cards, trans=None):
    migrate_cards(cards, migrate_cards.DETACHED, trans=trans)


class _MigrateCardsDetached(object):
    owner = None
    type = 'detached'


migrate_cards.SINGLE_LAYER = 1
migrate_cards.DETACHED = _MigrateCardsDetached()


def register_eh(cls):
    action_eventhandlers.add(cls)
    return cls
action_eventhandlers = set()

# ------------------------------------------


class GenericAction(Action): pass


class LaunchCardAction(object): pass


class UserAction(Action):  # card/character skill actions
    pass


class PlayerDeath(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.dead = True
        others = g.players.exclude(tgt)
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
                if g.process_action(LaunchHeal(p, tgt)):
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
        tgt.life -= self.amount
        return True


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


# ---------------------------------------------------

class DropCards(GenericAction):
    def __init__(self, target, cards, detached=False):
        self.target = target
        self.cards = cards
        self.detached = detached

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = self.cards
        assert all(c.resides_in.owner in (target, None) for c in cards), 'WTF?!'
        migrate_cards(cards, g.deck.droppedcards, unwrap=True, detached=self.detached)

        return True

    def is_valid(self):
        return True


class DropUsedCard(DropCards):
    pass


class UseCard(UserAction):
    card_usage = 'use'
    # launch_action = None

    def __init__(self, target):
        self.source = self.target = target
        self.card = None
        # self.cond = __subclass__.cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target

        if not self.card:  # ask if not already provided
            cards = user_choose_cards(self, target, ('cards', 'showncards'))
            if not cards or len(cards) != 1:
                self.card = None
                return False
            
            self.card = cards[0]

        if self.card_usage == 'launch':
            tgt = self.target
            act = self.launch_action(source=tgt, target=tgt)
            return launch_card(self, [], act)

        else:
            drop = DropUsedCard(target, cards=[self.card])
            g.process_action(drop)
            return True

    def cond(self, cl):
        raise NotImplementedError


class DropCardStage(GenericAction):
    card_usage = 'drop'

    def __init__(self, target):
        self.source = self.target = target
        self.dropn = len(target.cards) + len(target.showncards) - target.life
        self.cards = []

    def apply_action(self):
        target = self.target
        if target.dead: return False
        n = self.dropn
        if n <= 0: return True

        g = Game.getgame()
        cards = user_choose_cards(self, target, ('cards', 'showncards'))
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
        tgt = self.target
        if not len(cards) == self.dropn:
            return False

        if not all(c.resides_in in (tgt.cards, tgt.showncards) for c in cards):
            return False

        from .cards import Skill
        if any(c.is_card(Skill) for c in cards):
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


def launch_card(lca, target_list, action):
    assert isinstance(lca, LaunchCardAction)

    g = Game.getgame()
    src = lca.source
    card = lca.card
    try:
        if not getattr(card, 'no_move', False):
            detach_cards([card])

        _, tl = g.emit_event('choose_target', (lca, target_list))
        assert _ is lca

        if isinstance(action, Action):
            a = action
        else:
            assert issubclass(action, UserAction)

            tgt = tl[0] if tl else src
            a = action(source=src, target=tgt)
            a.target_list = tl

        a.associated_card = card
        lca.card_action = a

        _ = g.emit_event('post_choose_target', (lca, tl))
        assert _ == (lca, tl)

        return g.process_action(a)
    finally:

        if card.detached:
            # card/skill still in disputed state,
            # means no actions have done anything to the card/skill,
            # drop it
            if not getattr(card, 'no_drop', False):
                g.process_action(DropUsedCard(src, cards=[card], detached=True))
            else:
                from .cards import VirtualCard
                for c in VirtualCard.unwrap(card):
                    if c.detached: c.attach()


class LaunchCard(GenericAction, LaunchCardAction):
    def __init__(self, source, target_list, card):
        tl, tl_valid = card.target(Game.getgame(), source, target_list)
        self.source, self.target_list, self.card, self.tl_valid = source, tl, card, tl_valid
        self.target = target_list[0] if target_list else source

    def apply_action(self):
        card = self.card
        tl = self.target_list
        if not card: return False

        action = card.associated_action
        if not action: return False

        launch_card(self, tl, action)
        return True

    def is_valid(self):
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
        if not act.can_fire():
            log.debug('LaunchCard card_action.can_fire() FALSE')
            return False

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
    def calc_base_distance(cls, src):
        g = Game.getgame()
        pl = [p for p in g.players if not p.dead]
        loc = pl.index(src)
        n = len(pl)
        dist = {
            p: min(abs(i), n-abs(i))
            for p, i in zip(pl, xrange(-loc, -loc+n))
        }
        return dist


class ActionStageLaunchCard(LaunchCard):
    pass


@register_eh
class ShuffleHandler(EventHandler):
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
        #     act, cl, _from, to = arg
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


class ActionStage(GenericAction):
    card_usage = 'launch'

    def __init__(self, target):
        self.target = target
        self.in_user_input = False

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
                            self, [target], ('cards', 'showncards'), g.players, trans
                        )
                    check(p is target)
                finally:
                    self.in_user_input = False

                cards, target_list = rst
                g.players.reveal(cards)
                card = cards[0]

                if not g.process_action(ActionStageLaunchCard(target, target_list, card)):
                    # invalid input
                    log.debug('ActionStage: LaunchCard failed.')
                    break

        except CheckFailed:
            pass

        return True

    def cond(self, cl):
        from .cards import Skill
        if not cl: return False

        tgt = self.target
        if not len(cl) == 1:
            return False

        c = cl[0]
        return (
            c.is_card(Skill) or c.resides_in in (tgt.cards, tgt.showncards)
        ) and (c.associated_action)

    def choose_player_target(self, tl):
        return tl, True


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

    def apply_action(self):
        g = Game.getgame()
        card, = g.deck.getcards(1)
        g.players.reveal(card)
        self.card = card
        migrate_cards([card], g.deck.droppedcards)
        g.emit_event(self.type, self)
        return self.succeeded

    def set_card(self, card):
        self.card = card

    @property
    def succeeded(self):
        # This is necessary, for ui
        return self.cond(self.card)


class Fatetell(BaseFatetell):
    type = 'fatetell'


class TurnOverCard(BaseFatetell):
    type = 'turnover'


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
        a = act(source=target, target=target)
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


class PlayerTurn(GenericAction):
    def __init__(self, target):
        self.source = self.target = target

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        p.tags['turn_count'] += 1
        g.turn_count += 1
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
                cards = user_choose_cards(self, p, ('cards', 'showncards'), trans)
                if cards:
                    card = cards[0]
                else:
                    card = random_choose_card([p.cards, p.showncards])

                pindian_card[p] = card
                detach_cards([card])
                g.emit_event('pindian_card_chosen', (p, card))

        g.players.reveal([pindian_card[src], pindian_card[tgt]])
        g.emit_event('pindian_card_revealed', self)  # for ui.
        g.process_action(DropCards(src, [pindian_card[src]], detached=True))
        g.process_action(DropCards(tgt, [pindian_card[tgt]], detached=True))

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


@register_eh
class DyingHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseDamage): return act

        src = act.source
        tgt = act.target
        if tgt.dead or tgt.life > 0: return act

        g = Game.getgame()
        if g.process_action(TryRevive(tgt, dmgact=act)):
            return act

        g.process_action(PlayerDeath(src, tgt))

        return act


class ShowCards(GenericAction):
    def __init__(self, target, cards):
        self.source = self.target = target
        self.cards = cards

    def apply_action(self):
        if not self.cards:
            return False

        g = Game.getgame()
        cards = self.cards
        g.players.reveal(cards)
        g.emit_event('showcards', (self.target, cards))
        # user_input(
        #     [p for p in g.players if not p.dead],
        #     ChooseOptionInputlet(self, (True,)),
        #     type='all', timeout=1,
        # )  # just a delay
        return True
