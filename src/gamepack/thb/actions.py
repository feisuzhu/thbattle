# -*- coding: utf-8 -*-

# All generic and cards' Actions, EventHandlers are here
from game.autoenv import Game, EventHandler, Action
from game.autoenv import sync_primitive, user_input, InputTransaction

from .inputlets import ActionInputlet, ChoosePeerCardInputlet

from utils import check, check_type, CheckFailed, BatchList, group_by

import logging
log = logging.getLogger('THBattle_Actions')


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
        try:
            check(rst)
            skills, cards, players = rst
            [check(not c.detached) for c in cards]
            if categories:
                if skills:
                    # check(len(skills) == 1)  # why? disabling it.
                    # will reveal in skill_wrap
                    skill = skill_wrap(actor, skills, cards)
                    check(skill and initiator.cond([skill]))
                else:
                    if not getattr(initiator, 'no_reveal', False):
                        g.players.reveal(cards)

                    check(initiator.cond(cards))

            if candidates:
                players, valid = initiator.choose_player_target(players)
                check(valid)

            return skills, cards, players

        except CheckFailed:
            return None

    p, rst = user_input(actors, ilet, type='any', trans=trans)
    if rst:
        skills, cards, players = rst
        if skills:
            cards = [skill_transform(p, skills, cards)]

        if not cards and not players:
            return p, None

        [c.detach() for c in cards]

        return p, (cards, players)
    else:
        return None, None


def user_choose_cards(initiator, actor, categories):
    check_type([str, Ellipsis], categories)

    _, rst = ask_for_action(initiator, [actor], categories, [])
    if not rst:
        return None

    return rst[0]  # cards


def user_choose_players(initiator, actor, candidates):
    _, rst = ask_for_action(initiator, [actor], [], candidates)
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


def skill_wrap(actor, skills, cards, no_reveal=False, detach=False):
    # no_reveal: for ui
    g = Game.getgame()
    try:
        check(all(c.resides_in.owner is actor for c in cards))
        for skill_cls in skills:
            check(skill_cls in actor.skills)

            if not no_reveal and not getattr(skill_cls, 'no_reveal', False):
                g.players.exclude(actor).reveal(cards)

            card = skill_cls.wrap(cards, actor)
            check(card.check())

            detach and [c.detach() for c in cards]

            cards = [card]

        return cards[0]

    except CheckFailed:
        return None


def skill_transform(actor, skills, cards):
    g = Game.getgame()
    s = skill_wrap(actor, skills, cards, detach=True)
    if not s:
        return None

    g.deck.register_vcard(s)
    # migrate_cards(cards, actor.cards, False, True)
    # s.move_to(actor.cards)
    return s


def migrate_cards(cards, to, unwrap=False, no_event=False):
    g = Game.getgame()
    from .cards import VirtualCard
    groups = group_by(cards, lambda c: id(c) if c.is_card(VirtualCard) else id(c.resides_in))

    for l in groups:
        cl = l[0].resides_in
        for c in l:
            if unwrap and c.is_card(VirtualCard):
                # c.move_to(None)
                c.detach()  # resides_in should be consistent with normal cards
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
            g.emit_event('card_migration', (act, l, cl, to))  # (action, cardlist, from, to)

migrate_cards.SINGLE_LAYER = 2


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
                act = LaunchHeal(p, tgt)
                if g.process_action(act):
                    card = act.card
                    if not card: continue
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
    def __init__(self, target, cards):
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


class DropUsedCard(DropCards):
    pass


class UseCard(UserAction):
    def __init__(self, target):
        self.source = self.target = target
        # self.cond = __subclass__.cond

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        cards = user_choose_cards(self, target, ('cards', 'showncards'))

        if not cards or len(cards) != 1:
            self.card = None
            return False
        else:
            self.card = cards[0]
            drop = DropUsedCard(target, cards=cards)
            g.process_action(drop)
            return True

    @property
    def cards(self):
        raise Exception('obsolete')  # fail fast


class DropCardStage(GenericAction):
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

        action = card.associated_action
        if not action: return False

        try:
            target = target_list[0] if target_list else self.source
            a = action(source=self.source, target=target)
            self.card_action = a
            a.associated_card = card
            a.target_list = target_list

            card.detach()
            g.emit_event('before_launch_card', self)
            g.process_action(a)
        finally:
            if card.detached:
                # card/skill still in disputed state,
                # means no actions have done anything to the card/skill,
                # drop it
                if not getattr(card, 'no_drop', False):
                    g.process_action(DropUsedCard(self.source, cards=[card]))
                else:
                    # cards are detached here, denotes disputed state.
                    # can cause problems when skill declares 'no_drop'
                    # so revert the detached state.
                    from .cards import VirtualCard
                    [c.attach() for c in VirtualCard.unwrap([card])]

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
                    self.in_user_input = True
                    g.emit_event('action_stage_action', target)
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

        pl = BatchList([src, tgt])
        pindian_card = {src: None, tgt: None}

        with InputTransaction('Pindian', pl) as trans:
            while pl:
                p, rst = ask_for_action(self, pl, ['cards', 'showncards'], [], trans)
                if not p: break
                (card, ), _ = rst
                pindian_card[p] = card
                g.emit_event('pindian_card_chosen', (p, card))

            # not chosen
            for p in pl:
                pindian_card[p] = card = random_choose_card([p.cards, p.showncards])
                g.emit_event('pindian_card_chosen', (p, card))

        g.players.reveal([pindian_card[src], pindian_card[tgt]])
        g.process_action(DropCards(src, [pindian_card[src]]))
        g.process_action(DropCards(pl[1], [pindian_card[tgt]]))

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
