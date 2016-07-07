# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from copy import copy
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, get_seed_for
from game.autoenv import user_input
from game.base import sync_primitive
from thb.actions import ActionStageLaunchCard, AskForCard, DistributeCards, DrawCards, DropCardStage
from thb.actions import DropCards, GenericAction, LifeLost, PlayerDeath, PlayerTurn, RevealIdentity
from thb.actions import TryRevive, UserAction, action_eventhandlers, ask_for_action, ttags
from thb.cards import AttackCard, AttackCardHandler, GrazeCard, Heal, Skill, TreatAs, VirtualCard
from thb.cards import t_None, t_One
from thb.characters.baseclasses import mixin_character
from thb.common import PlayerIdentity, build_choices
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet
from thb.item import ImperialIdentity
from utils.misc import BatchList, Enum, classmix, first


# -- code --
log = logging.getLogger('THBattleIdentity')
_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class IdentityRevealHandler(EventHandler):
    interested = ('action_apply', )
    execute_before = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()
            tgt = act.target

            g.process_action(RevealIdentity(tgt, g.players))

        return act


@game_eh
class DeathHandler(EventHandler):
    interested = ('action_apply', 'action_after')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = Game.getgame()
            T = Identity.TYPE

            tgt = act.target
            dead = lambda p: p.dead or p is tgt

            # curtain's win
            survivors = [p for p in g.players if not dead(p)]
            if len(survivors) == 1:
                pl = g.players
                pl.reveal([p.identity for p in g.players])

                if survivors[0].identity.type == T.CURTAIN:
                    g.winners = survivors[:]
                    g.game_end()

            deads = defaultdict(list)
            for p in g.players:
                if dead(p):
                    deads[p.identity.type].append(p)

            def winner(*identities):
                pl = g.players
                pl.reveal([p.identity for p in g.players])

                g.winners = [p for p in pl if p.identity.type in identities]
                g.game_end()

            def no(identity):
                return len(deads[identity]) == g.identities.count(identity)

            # attackers' & curtain's win
            if len(deads[T.BOSS]):
                if g.double_curtain:
                    winner(T.ATTACKER)
                else:
                    if no(T.ATTACKER):
                        winner(T.CURTAIN)
                    else:
                        winner(T.ATTACKER)

            # boss & accomplices' win
            if no(T.ATTACKER) and no(T.CURTAIN):
                winner(T.BOSS, T.ACCOMPLICE)

            # all survivors dropped
            if all([p.dropped for p in survivors]):
                pl = g.players
                pl.reveal([p.identity for p in pl])
                g.winners = []
                g.game_end()

        elif evt_type == 'action_after' and isinstance(act, PlayerDeath):
            T = Identity.TYPE
            g = Game.getgame()
            tgt = act.target
            src = act.source

            if src:
                if tgt.identity.type == T.ATTACKER:
                    g.process_action(DrawCards(src, 3))
                elif tgt.identity.type == T.ACCOMPLICE:
                    if src.identity.type == T.BOSS:
                        g.players.exclude(src).reveal(list(src.cards))

                        cards = []
                        cards.extend(src.cards)
                        cards.extend(src.showncards)
                        cards.extend(src.equips)
                        cards and g.process_action(DropCards(src, src, cards))

        return act


class AssistedAttackCard(TreatAs, VirtualCard):
    treat_as = AttackCard


class AssistedAttackAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        pl = [p for p in g.players if not p.dead and p is not src]
        p, rst = ask_for_action(self, pl, ('cards', 'showncards'), [], timeout=6)
        if not p:
            ttags(src)['assisted_attack_disable'] = True
            return False

        (c,), _ = rst
        g.process_action(ActionStageLaunchCard(src, [tgt], AssistedAttackCard.wrap([c], src)))

        return True

    def cond(self, cl):
        return len(cl) == 1 and cl[0].is_card(AttackCard)

    def is_valid(self):
        src, tgt = self.source, self.target
        act = ActionStageLaunchCard(src, [tgt], AttackCard())
        disabled = ttags(src)['assisted_attack_disable']
        return not disabled and AttackCardHandler.can_launch_attack(src) and act.can_fire()


class AssistedAttack(Skill):
    associated_action = AssistedAttackAction
    target = t_One
    skill_category = ('character', 'active', 'boss')
    distance = 1

    def check(self):
        return not self.associated_cards


class AssistedGraze(Skill):
    associated_action = None
    target = t_None
    skill_category = ('character', 'passive', 'boss')


class DoNotProcessCard(object):

    def process_card(self, c):
        return True


class AssistedUseAction(UserAction):
    def __init__(self, target, afc):
        self.source = self.target = target
        self.their_afc_action = afc

    def apply_action(self):
        tgt = self.target
        g = Game.getgame()

        pl = BatchList([p for p in g.players if not p.dead])
        pl = pl.rotate_to(tgt)[1:]
        rst = user_input(pl, ChooseOptionInputlet(self, (False, True)), timeout=6, type='all')

        afc = self.their_afc_action
        for p in pl:
            if p in rst and rst[p]:
                act = copy(afc)
                act.__class__ = classmix(DoNotProcessCard, afc.__class__)
                act.target = p
                if g.process_action(act):
                    self.their_afc_action.card = act.card
                    return True
        else:
            return False

        return True


class AssistedUseHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, AskForCard):
            tgt = act.target
            if not (tgt.has_skill(self.skill) and issubclass(act.card_cls, self.card_cls)):
                return act

            if isinstance(act, DoNotProcessCard):
                return act

            self.assist_target = tgt
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g = Game.getgame()
            g.process_action(AssistedUseAction(tgt, act))

        return act


@game_eh
class AssistedAttackHandler(AssistedUseHandler):
    skill = AssistedAttack
    card_cls = AttackCard


@game_eh
class AssistedAttackRangeHandler(AssistedUseHandler):
    interested = ('calcdistance', )

    def handle(self, evt_type, arg):
        src, card, dist = arg
        if evt_type == 'calcdistance':
            if card.is_card(AssistedAttack):
                AttackCardHandler.fix_attack_range(src, dist)

        return arg


@game_eh
class AssistedGrazeHandler(AssistedUseHandler):
    skill = AssistedGraze
    card_cls = GrazeCard


class AssistedHealAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(Heal(src, tgt))
        g.process_action(LifeLost(src, src))
        return True


@game_eh
class AssistedHealHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, TryRevive):
            if not act.succeeded:
                return act

            tgt = act.target
            if not tgt.has_skill(AssistedHeal):
                return act

            self.good_person = p = act.revived_by  # for ui

            if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                return act

            g = Game.getgame()
            g.process_action(AssistedHealAction(p, tgt))

        return act


class AssistedHeal(Skill):
    associated_action = None
    target = t_None
    skill_category = ('character', 'passive', 'boss')


@game_eh
class ExtraCardSlotHandler(EventHandler):
    interested = ('action_before',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if not tgt.has_skill(ExtraCardSlot):
                return act

            g = Game.getgame()
            n = sum(i == Identity.TYPE.ACCOMPLICE for i in g.identities)
            n -= sum(p.dead and p.identity.type == Identity.TYPE.ACCOMPLICE for p in g.players)
            act.dropn = max(act.dropn - n, 0)

        return act


class ExtraCardSlot(Skill):
    associated_action = None
    target = t_None
    skill_category = ('character', 'passive', 'boss')


class Identity(PlayerIdentity):
    # 城管 BOSS 道中 黑幕
    class TYPE(Enum):
        HIDDEN = 0
        ATTACKER = 1
        BOSS = 4
        ACCOMPLICE = 2
        CURTAIN = 3


class ChooseBossSkillAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        if hasattr(tgt, 'boss_skills'):
            bs = tgt.boss_skills
            assert len(bs) == 1
            tgt.skills.extend(bs)
            self.skill_chosen = bs[0]
            return True

        self.boss_skills = l = [  # for ui
            AssistedAttack,
            AssistedGraze,
            AssistedHeal,
            ExtraCardSlot,
        ]
        rst = user_input([tgt], ChooseOptionInputlet(self, [i.__name__ for i in l]))
        rst = first(l, lambda i: i.__name__ == rst) or first(l)
        tgt.skills.append(rst)
        self.skill_chosen = rst  # for ui
        return True


class THBattleIdentityBootstrap(GenericAction):
    def __init__(self, params, items):
        self.source = self.target = None
        self.params = params
        self.items = items

    def apply_action(self):
        g = Game.getgame()
        params = self.params

        from thb.cards import Deck

        g.deck = Deck(ppoints=(1, 1, 1, 1, 1, 1, 2, 2))
        g.ehclasses = []

        # arrange identities -->
        g.double_curtain = params['double_curtain']

        mapping = {
            'B': Identity.TYPE.BOSS,
            '!': Identity.TYPE.ATTACKER,
            '&': Identity.TYPE.ACCOMPLICE,
            '?': Identity.TYPE.CURTAIN,
        }

        if g.double_curtain:
            identities = 'B!!!&&??'
        else:
            identities = 'B!!!!&&?'

        pl = g.players[:]
        identities = [mapping[i] for i in identities]
        g.identities = identities[:]
        imperial_identities = ImperialIdentity.get_chosen(self.items, pl)
        for p, i in imperial_identities:
            pl.remove(p)
            identities.remove(i)

        g.random.shuffle(identities)

        if Game.CLIENT_SIDE:
            identities = [Identity.TYPE.HIDDEN for _ in identities]

        for p, i in imperial_identities + zip(pl, identities):
            p.identity = Identity()
            p.identity.type = i
            g.process_action(RevealIdentity(p, p))

        del identities

        is_boss = sync_primitive([p.identity.type == Identity.TYPE.BOSS for p in g.players], g.players)
        boss_idx = is_boss.index(True)
        boss = g.boss = g.players[boss_idx]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS
        g.process_action(RevealIdentity(boss, g.players))

        # choose girls init -->
        from .characters import get_characters
        chars = get_characters('common', 'id', 'id8')

        pl = g.players.rotate_to(boss)

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=[boss],
            num=[5], akaris=[1],
            shared=False,
        )

        with InputTransaction('ChooseGirl', [boss], mapping=choices) as trans:
            c = user_input([boss], ChooseGirlInputlet(g, choices), 30, 'single', trans)

            c = c or choices[boss][-1]
            c.chosen = boss
            c.akari = False
            g.players.reveal(c)
            trans.notify('girl_chosen', (boss, c))

        try:
            chars.remove(c.char_cls)
        except:
            pass

        # mix it in advance
        # so the others could see it

        boss = g.switch_character(boss, c.char_cls)

        # boss's hp bonus
        if g.n_persons > 5:
            boss.maxlife += 1

        boss.life = boss.maxlife

        # choose boss dedicated skill
        g.process_action(ChooseBossSkillAction(boss, boss))

        # reseat
        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(g.players)
        g.emit_event('reseat', None)

        # others choose girls
        pl = g.players.exclude(boss)

        choices, _ = build_choices(
            g, self.items,
            candidates=chars, players=pl,
            num=[4] * len(pl), akaris=[1] * len(pl),
            shared=False,
        )

        with InputTransaction('ChooseGirl', pl, mapping=choices) as trans:
            ilet = ChooseGirlInputlet(g, choices)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            result = user_input(pl, ilet, type='all', trans=trans)

        # mix char class with player -->
        for p in pl:
            c = result[p] or choices[p][-1]
            c.akari = False
            g.players.reveal(c)
            p = g.switch_character(p, c.char_cls)

        # -------
        for p in g.players:
            log.info(
                u'>> Player: %s:%s %s',
                p.__class__.__name__,
                Identity.TYPE.rlookup(p.identity.type),
                p.account.username,
            )
        # -------

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=4))

        for i, p in enumerate(cycle(g.players.rotate_to(boss))):
            if i >= 6000: break
            if not p.dead:
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

        return True


class THBattleIdentity(Game):
    n_persons = 8
    game_ehs = _game_ehs
    bootstrap = THBattleIdentityBootstrap
    params_def = {
        'double_curtain': (False, True),
    }

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def switch_character(g, p, cls):
        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)

        ehs = g.ehclasses
        assert not oldcls
        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()
        g.emit_event('switch_character', (old, p))

        return p

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.set_event_handlers(EventHandler.make_list(ehclasses))

    def decorate(self, p):
        from thb.cards import CardList
        p.cards          = CardList(p, 'cards')        # Cards in hand
        p.showncards     = CardList(p, 'showncards')   # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')       # Equipments
        p.fatetell       = CardList(p, 'fatetell')     # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')      # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]  # cardlists should shown to others
        p.tags           = defaultdict(int)

    def get_stats(g):
        return [{'event': 'pick', 'attributes': {
            'character': p.__class__.__name__,
            'gamemode': g.__class__.__name__,
            'identity': Identity.TYPE.rlookup(p.identity.type),
            'victory': p in g.winners,
        }} for p in g.players]
