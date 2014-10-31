# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import logging
import random

# -- third party --
# -- own --
from .actions import ActionStage, ActionStageLaunchCard, BaseDamage, Damage, DeadDropCards
from .actions import DistributeCards, DrawCards, DropCards, GenericAction, LaunchCard, LifeLost
from .actions import MaxLifeChange, PlayerDeath, PlayerRevive, PlayerTurn, RevealIdentity
from .actions import UserAction, action_eventhandlers, migrate_cards, user_choose_cards
from .cards import Skill, t_None
from .characters.baseclasses import mixin_character
from .common import CharChoice, PlayerIdentity, get_seed_for
from .inputlets import ChooseGirlInputlet, ChooseIndividualCardInputlet, ChooseOptionInputlet
from game.autoenv import EventHandler, Game, GameException, InputTransaction, InterruptActionFlow
from game.autoenv import user_input
from utils import BatchList, Enum

# -- code --
log = logging.getLogger('THBattleRaid')

_game_ehs = {}
_game_actions = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


def game_action(cls):
    _game_actions[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DeadDropCards):
            tgt = act.target
            g = Game.getgame()

            # attackers' win
            if tgt is g.mutant:
                g.winners = g.attackers
                g.game_end()

            # mutant's win
            if all(p.dead for p in g.attackers):
                g.winners = [g.mutant]
                g.game_end()

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            tgt = act.target
            g = Game.getgame()

            if tgt in g.attackers:
                for p in [p for p in g.attackers if not p.dead]:
                    if user_input([p], ChooseOptionInputlet(self, (False, True))):
                        g.process_action(DrawCards(p, 1))

        return act


def use_faith(target, amount=1):
    g = Game.getgame()
    assert amount <= len(target.faiths)
    if len(target.faiths) == amount:
        g.process_action(DropCards(target, list(target.faiths)))
        return

    for i in xrange(amount):
        c = user_input([target], ChooseIndividualCardInputlet(None, target.faiths))
        if not c: break
        g.process_action(DropCards(target, [c]))
        amount -= 1

    if amount:
        g.process_action(DropCards(target, list(target.faiths)[:amount]))


class CollectFaith(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt = self.target

        g = Game.getgame()

        amount = max(0, 5 - len(tgt.faiths))
        amount = min(amount, self.amount)

        if not amount: return False

        cards = g.deck.getcards(amount)
        g.players.reveal(cards)
        migrate_cards(cards, tgt.faiths)
        self.cards = cards

        return True


@game_eh
class CollectFaithHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_apply': return act
        if not isinstance(act, Damage): return act
        src = act.source
        if not src: return act

        g = Game.getgame()
        g.process_action(CollectFaith(src, src, act.amount))
        return act


class CooperationAction(UserAction):
    card_usage = 'handover'

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        src.tags['cooperation_tag'] = src.tags['turn_count']
        skill = self.associated_card
        self.ncards = len(skill.associated_cards)

        migrate_cards([skill], tgt.showncards, unwrap=True)

        returned = user_choose_cards(self, tgt, ['cards', 'showncards'])
        if not returned:
            returned = (list(tgt.showncards) + list(tgt.cards))[:self.ncards]

        g.players.reveal(returned)
        migrate_cards(returned, src.showncards)

        return True

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['cooperation_tag']

    def cond(self, cl):
        if not len(cl) == self.ncards: return False
        tgt = self.target
        return all(c.resides_in in (tgt.cards, tgt.showncards) for c in cl)


class Cooperation(Skill):
    associated_action = CooperationAction
    skill_category = ('active',)
    no_drop = True
    usage = 'handover'

    def target(self, g, src, tl):
        attackers = g.attackers
        tl = [p for p in tl if not p.dead and p is not src and p in attackers]
        return (tl[-1:], bool(len(tl)))

    def check(self):
        cl = self.associated_cards
        if not cl: return False
        if not len(cl) <= 2: return False
        return all(c.resides_in is not None and c.resides_in.type in (
            'cards', 'showncards',
        ) for c in cl)


class Protection(Skill):
    associated_action = None
    skill_category = ('passive',)
    target = t_None


class ProtectionAction(GenericAction):
    def __init__(self, source, dmgact):
        self.source = source
        self.target = dmgact.target
        self.dmgact = dmgact

    def apply_action(self):
        g = Game.getgame()
        src = self.source

        use_faith(src, 1)

        act = self.dmgact
        act.cancelled = True

        g.process_action(LifeLost(src, src, act.amount))
        g.process_action(CollectFaith(g.mutant, g.mutant, 1))

        return True


@game_eh
class ProtectionHandler(EventHandler):
    execute_before = ('WineHandler', )
    execute_after = ('RepentanceStickHandler', )

    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, Damage): return act
        if act.cancelled: return act

        g = Game.getgame()
        tgt = act.target

        pl = g.attackers[:]
        if tgt not in pl: return act
        if tgt.life != min([p.life for p in pl if not p.dead]): return act

        g = Game.getgame()
        pl.remove(tgt)

        self.dmgact = act

        pl = [p for p in pl if not p.dead and len(p.faiths) and p.has_skill(Protection)]
        for p in pl:
            if user_input([p], ChooseOptionInputlet(self, (False, True))):
                g.process_action(ProtectionAction(p, act))
                break

        return act


class Parry(Skill):
    associated_action = None
    skill_category = ('passive',)
    target = t_None


class ParryAction(GenericAction):
    def __init__(self, source, dmgact):
        self.source = source
        self.target = dmgact.target
        self.dmgact = dmgact

    def apply_action(self):
        use_faith(self.source, 2)
        self.dmgact.amount -= 1
        return True


@game_eh
class ParryHandler(EventHandler):
    execute_before = ('ProtectionHandler', )
    execute_after = ('RepentanceStickHandler', )

    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, Damage): return act
        tgt = act.target
        if not tgt.has_skill(Parry): return act
        if not len(tgt.faiths) >= 2: return act
        if not (act.amount >= 2 or tgt.life <= act.amount): return act

        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        g = Game.getgame()
        g.process_action(ParryAction(tgt, act))

        return act


@game_eh
class RaidPlayerReviveHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, PlayerRevive): return act
        tgt = act.target
        tgt.skills.extend([
            Cooperation, Protection, Parry,
        ])

        if not tgt.tags['oneup_used']:
            tgt.skills.append(OneUp)

        return act


class OneUpAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        g = Game.getgame()
        assert tgt.dead, 'WTF?!'
        assert tgt in g.attackers

        use_faith(src, 3)
        src.skills.remove(OneUp)
        src.tags['oneup_used'] = True

        g.process_action(PlayerRevive(tgt, tgt, 3))
        tgt.tags['action'] = True

        return True

    def is_valid(self):
        return self.target.dead


class OneUp(Skill):
    associated_action = OneUpAction
    skill_category = ('active',)

    def target(self, g, src, tl):
        attackers = g.attackers
        tl = [p for p in tl if p.dead and p in attackers]
        return (tl[-1:], bool(len(tl)))

    def check(self):
        if len(self.player.faiths) < 3: return False
        return not self.associated_cards


class FaithExchange(UserAction):
    card_usage = 'move_out'

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        n = 0
        for i in xrange(len(tgt.faiths)):
            c = user_input([tgt], ChooseIndividualCardInputlet(None, tgt.faiths))
            if not c: break
            migrate_cards([c], tgt.showncards)
            n += 1

        if not n:
            return True

        self.amount = n

        cards = user_choose_cards(self, tgt, ['cards', 'showncards'])
        if not cards:
            cards = list(tgt.showncards)[:self.amount]

        g.players.reveal(cards)
        migrate_cards(cards, tgt.faiths)

        return True

    def cond(self, cl):
        return len(cl) == self.amount


@game_eh
class FaithExchangeHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_before': return act
        if not isinstance(act, ActionStage): return act
        g = Game.getgame()
        tgt = act.target
        if not tgt.faiths: return act
        g.process_action(FaithExchange(tgt, tgt))
        return act


class Identity(PlayerIdentity):
    # 异变 解决者
    class TYPE(Enum):
        HIDDEN = 0
        MUTANT = 1
        ATTACKER = 2


class RaidLaunchCard(LaunchCard):
    @classmethod
    def calc_base_distance(cls, src):
        g = Game.getgame()
        return {p: 1 for p in g.players}


class RaidActionStageLaunchCard(RaidLaunchCard, ActionStageLaunchCard):
    pass


class RequestAction(object):  # for choose_option
    pass


class GetFaith(object):  # for choose_option
    pass


class MutantMorph(GameException):
    pass


@game_eh
class MutantMorphHandler(EventHandler):
    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseDamage): return act
        g = Game.getgame()
        tgt = act.target
        if tgt is not g.mutant: return act
        if tgt.morphed: return act

        if tgt.life <= tgt.__class__.maxlife // 2:
            raise MutantMorph

        return act


class THBattleRaid(Game):
    n_persons    = 4
    game_actions = _game_actions
    game_ehs     = _game_ehs
    params_def   = {
        'random_seat': (False, True),
    }

    def game_start(g, params):
        # game started, init state

        g.action_types[LaunchCard] = RaidLaunchCard
        g.action_types[ActionStageLaunchCard] = RaidActionStageLaunchCard

        g.ehclasses = []

        if params['random_seat']:
            seed = get_seed_for(g.players)
            random.Random(seed).shuffle(g.players)
            g.emit_event('reseat', None)

        # reveal identities
        mutant = g.mutant = g.players[0]
        attackers = g.attackers = BatchList(g.players[1:])

        mutant.identity = Identity()
        mutant.identity.type = Identity.TYPE.MUTANT

        g.process_action(RevealIdentity(mutant, g.players))

        for p in attackers:
            p.identity = Identity()
            p.identity.type = Identity.TYPE.ATTACKER

            g.process_action(RevealIdentity(p, g.players))

        from characters import get_characters

        # mutant's choose
        raid_chars = get_characters('raid_ex', '-common')

        choices = [CharChoice(cls) for cls in raid_chars]
        mapping = {mutant: choices}
        with InputTransaction('ChooseGirl', [mutant], mapping=mapping) as trans:
            c = user_input([mutant], ChooseGirlInputlet(g, mapping), timeout=5, trans=trans)
            c = c or choices[0]
            c.chosen = mutant
            trans.notify('girl_chosen', (mutant, c))

            # mix it in advance
            # so the others could see it

            g.mutant = mutant = g.switch_character(mutant, c.char_cls)

            mutant.life = mutant.maxlife
            mutant.morphed = False

        # init deck & mutant's initial equip
        # (SinsackCard, SPADE, 1)
        # (SinsackCard, HEART, Q)
        from cards import Deck, SinsackCard, ElementalReactorCard, card_definition
        raid_carddef = [
            carddef for carddef in card_definition
            if carddef[0] not in (SinsackCard, ElementalReactorCard)
        ]

        g.deck = Deck(raid_carddef)

        # attackers' choose
        chars = get_characters('raid')
        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(chars)

        for p in g.attackers:
            p.choices = [CharChoice(cls) for cls in chars[:5]]
            del chars[:5]

        # -----------
        mapping = {p: p.choices for p in g.attackers}
        with InputTransaction('ChooseGirl', g.attackers, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            result = user_input(g.attackers, ilet, 30, 'all', trans)

        # mix char class with player -->
        for p in g.attackers:
            c = result[p] or CharChoice(chars.pop())
            c.chosen = p
            p = g.switch_character(p, c.char_cls)
            p.skills.extend([
                Cooperation, Protection,
                Parry, OneUp,
            ])

        g.update_event_handlers()

        g.emit_event('game_begin', g)

        # -------
        log.info(u'>> Game info: ')
        log.info(u'>> Mutant: %s', mutant.__class__.__name__)
        for p in attackers:
            log.info(u'>> Attacker: %s', p.__class__.__name__)

        # -------

        g.process_action(DistributeCards(mutant, amount=6))
        for p in attackers:
            g.process_action(DistributeCards(p, amount=4))

        # stage 1
        try:
            for i in xrange(500):
                g.process_action(CollectFaith(mutant, mutant, 1))

                avail = [p for p in attackers if not p.dead and len(p.faiths) < 5]
                if avail:
                    p, _ = user_input(
                        avail,
                        ChooseOptionInputlet(GetFaith, (None, True)),
                        type='any',
                    )
                    p = p or avail[0]
                    g.process_action(CollectFaith(p, p, 1))

                g.emit_event('round_start', False)

                for p in attackers:
                    p.tags['action'] = True

                while True:
                    try:
                        g.process_action(PlayerTurn(mutant))
                    except InterruptActionFlow:
                        pass

                    avail = BatchList([p for p in attackers if p.tags['action'] and not p.dead])
                    if not avail:
                        break

                    p, _ = user_input(
                        avail,
                        ChooseOptionInputlet(RequestAction, (None, True)),
                        type='any',
                    )

                    p = p or avail[0]
                    p.tags['action'] = False

                    try:
                        g.process_action(PlayerTurn(p))
                    except InterruptActionFlow:
                        pass

                    del p  # mute linter
                    if not [p for p in attackers if p.tags['action'] and not p.dead]:
                        break

        except MutantMorph:
            pass

        # morphing
        stage1 = mutant.__class__
        stage2 = stage1.stage2

        for s in stage1.skills:
            try:
                mutant.skills.remove(s)
            except ValueError:
                pass

        mutant.skills.extend(stage2.skills)

        ehclasses = g.ehclasses
        for s in stage1.eventhandlers_required:
            try:
                ehclasses.remove(s)
            except ValueError:
                pass

        ehclasses.extend(stage2.eventhandlers_required)

        g.process_action(
            MaxLifeChange(mutant, mutant, -(stage1.maxlife // 2))
        )
        mutant.morphed = True

        mutant.__class__ = stage2

        g.update_event_handlers()

        for p in attackers:
            g.process_action(CollectFaith(p, p, 1))

        g.process_action(DropCards(mutant, mutant.fatetell))

        g.emit_event('mutant_morph', mutant)

        g.pause(4)

        # stage 2
        for i in xrange(500):
            g.process_action(CollectFaith(mutant, mutant, 1))

            avail = [p for p in attackers if not p.dead and len(p.faiths) < 5]
            if avail:
                p, _ = user_input(
                    avail,
                    ChooseOptionInputlet(GetFaith, (None, True)),
                    type='any',
                )
                p = p or avail[0]
                g.process_action(CollectFaith(p, p, 1))

            g.emit_event('round_start', False)

            for p in attackers:
                p.tags['action'] = True

            try:
                g.process_action(PlayerTurn(mutant))
            except InterruptActionFlow:
                pass

            while True:
                avail = BatchList([p for p in attackers if p.tags['action'] and not p.dead])
                if not avail:
                    break

                p, _ = user_input(
                    avail,
                    ChooseOptionInputlet(RequestAction, (None, True)),
                    type='any'
                )

                p = p or avail[0]

                p.tags['action'] = False
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

    def can_leave(self, p):
        return False

    def switch_character(g, p, cls):
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)
        g.attackers.replace(old, p)

        ehs = g.ehclasses
        ehs.extend(p.eventhandlers_required)
        g.emit_event('switch_character', p)

        return p

    def update_event_handlers(self):
        ehclasses = list(action_eventhandlers) + self.game_ehs.values()
        ehclasses += self.ehclasses
        self.event_handlers = EventHandler.make_list(ehclasses)

    def decorate(self, p):
        from cards import CardList
        p.cards = CardList(p, 'cards')  # Cards in hand
        p.showncards = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips = CardList(p, 'equips')  # Equipments
        p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
        p.faiths = CardList(p, 'faiths')  # 'faith' cards
        p.special = CardList(p, 'special')  # used on special purpose

        p.showncardlists = [p.showncards, p.faiths, p.fatetell]  # cardlists should shown to others

        p.tags = defaultdict(int)
        p.tags['faithcounter'] = True  # for ui
