# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from itertools import chain, combinations, cycle
import logging
import random

# -- third party --
# -- own --
from .actions import ActionStageLaunchCard, Damage, DistributeCards, DrawCards, DropCardStage
from .actions import PlayerDeath, PlayerRevive, PlayerTurn, RevealIdentity, UserAction
from .actions import action_eventhandlers, skill_wrap
from .cards import AttackCard, DelayedSpellCardAction, DonationBoxCard, HealCard, NazrinRodCard
from .characters.baseclasses import mixin_character
from .characters.koakuma import Find
from .common import CharChoice, PlayerIdentity
from .inputlets import ActionInputlet, ChooseGirlInputlet, ChooseOptionInputlet
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, NPC
from game.autoenv import sync_primitive, user_input
from utils import BatchList, Enum, filter_out
import settings


# -- code --
log = logging.getLogger('THBattleBook')

_game_ehs = {}


def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls


@game_eh
class VictoryHandler(EventHandler):
    interested = (
        ('action_before', (PlayerDeath, Damage)),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerDeath):
            g = Game.getgame()

            tgt = act.target
            if tgt is not g.koakuma: return act

            hakurei, moriya = g.forces
            books = lambda force: sum(p.tags['books'] for p in force)
            nh, nm = books(hakurei), books(moriya)
            if nh > nm:
                g.winners = hakurei
            elif nh < nm:
                g.winners = moriya
            else:
                g.winners = hakurei + moriya

            g.game_end()

        elif evt_type == 'action_after' and isinstance(act, Damage):
            g = Game.getgame()

            hakurei, moriya = g.forces
            books = lambda force: sum(p.tags['books'] for p in force)

            if books(hakurei) >= g.total_books:
                g.winners = hakurei
                g.game_end()

            elif books(moriya) >= g.total_books:
                g.winners = moriya
                g.game_end()

        return act


@game_eh
class BookCardUpperLimitHandler(EventHandler):
    interested = (
        ('action_before', DropCardStage),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            g = Game.getgame()
            if tgt is g.koakuma: return act
            n = min(tgt.tags['books'], 3)
            act.dropn = max(act.dropn - n, 0)

        return act


class BookShootdownCompromise(UserAction):
    def __init__(self, dmg):
        self.source = dmg.target
        self.target = dmg.source
        self.dmg = dmg

    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        g.process_action(GrabBooks(tgt, src, 2))
        self.dmg.amount -= 1
        return True


@game_eh
class BookShootdownCompromiseHandler(EventHandler):
    interested = (
        ('action_before', Damage),
    )

    execute_after = ('WineHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            tgt = act.target
            if act.source is None: return act
            if act.amount < tgt.life: return act
            if tgt.tags['books'] < 2: return act
            g = Game.getgame()
            if tgt is g.koakuma: return act
            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(BookShootdownCompromise(act))

        return act


@game_eh
class BookTransferHandler(EventHandler):
    interested = (
        ('action_after', Damage),
        ('action_apply', PlayerDeath),
    )

    execute_before = ('DyingHandler', 'VictoryHandler')

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if src and tgt.tags['books'] > 0 and act.amount > 0:
                if user_input([src], ChooseOptionInputlet(self, (False, True))):
                    g = Game.getgame()
                    g.process_action(GrabBooks(src, tgt, min(tgt.tags['books'], act.amount)))

        elif evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            src, tgt = act.source, act.target
            g = Game.getgame()

            if src is tgt or not src:
                src = g.koakuma

            if tgt.tags['books'] > 0:
                g.process_action(GrabBooks(src, tgt, tgt.tags['books']))

        return act


@game_eh
class InvalidateDelayedSpellcard(EventHandler):
    interested = (
        ('action_before', DelayedSpellCardAction),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DelayedSpellCardAction):
            tgt = act.target
            if tgt is Game.getgame().koakuma:
                act.cancelled = True

        return act


class GrabBooks(UserAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        src, tgt, a = self.source, self.target, self.amount
        assert a <= tgt.tags['books']
        tgt.tags['books'] -= a
        src.tags['books'] += a
        return True


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN  = 0
        HAKUREI = 1
        MORIYA  = 2
        ADMIN   = 3


class KoakumaAI(object):

    def __init__(self, trans, ilet):
        self.trans = trans
        self.ilet = ilet

    def entry(self):
        ilet = self.ilet
        trans = self.trans
        p = ilet.actor

        g = Game.getgame()
        g.pause(1.2)

        if trans.name == 'ActionStageAction':
            tl = self.get_optimal_targets()
            cl = list(p.showncards) + list(p.cards)

            for c in cl:
                if ('equipment' in c.category and c.equipment_category != 'greenufo'):
                    cat = c.equipment_category
                    if cat not in [i.equipment_category for i in p.equips] or cat == 'weapon':
                        if self.try_launch(c, [p]): return True

                if c.is_card(HealCard) or c.is_card(NazrinRodCard):
                    if self.try_launch(c, [p]): return True

            if len(cl) > 2 and tl[0].tags['books']:
                for c in cl:
                    if 'delayed_spellcard' in c.category:
                        continue

                    if c.is_card(DonationBoxCard):
                        if self.try_launch(c, tl[:2]): return True

                    if 'spellcard' in c.category:
                        if self.try_launch(c, tl[:1]): return True

            if self.try_skill_find(): return True

            if tl[0].tags['books']:
                for c in cl:
                    if c.is_card(AttackCard):
                        if self.try_launch(c, tl[:1]): return True

        elif trans.name == 'Action' and isinstance(ilet, ActionInputlet):
            if not (ilet.categories and not ilet.candidates):
                return True

            cond = ilet.initiator.cond
            cl = list(p.showncards) + list(p.cards)
            _, C = chain, lambda r: combinations(cl, r)
            for c in _(C(1), C(2)):
                if cond(c):
                    ilet.set_result(skills=[], cards=c, players=[])
                    return True

        elif trans.name == 'ChooseOption':
            if True in ilet.options:
                ilet.set_option(True)
            else:
                ilet.set_option(ilet.options[0])

            return True

    def try_launch(self, c, tl, skills=[]):
        p = self.ilet.actor
        act = ActionStageLaunchCard(p, tl, c)
        if act.can_fire():
            self.ilet.set_result(skills=skills, cards=[c], players=tl)
            return True

        return False

    def try_skill_find(self):
        p = self.ilet.actor
        cl = list(p.cards) + list(p.showncards)
        wrapped = skill_wrap(p, [Find], cl, {})
        act = ActionStageLaunchCard(p, [p], wrapped)
        if act.can_fire():
            self.ilet.set_result(skills=[Find], cards=cl, players=[p])
            return True

        return False

    def get_optimal_targets(self):
        g = Game.getgame()
        pl = g.players[1:]
        pl.sort(key=lambda p: (p.tags['books'], p.life, random.random()), reverse=True)
        return pl

    @classmethod
    def ai_main(cls, trans, ilet):
        cls(trans, ilet).entry()


class THBattleBook(Game):
    n_persons    = 4
    game_ehs     = _game_ehs
    npc_players  = [NPC(u'小恶魔', KoakumaAI.ai_main)]
    params_def   = {}
    total_books  = 7

    def game_start(g, params):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = list(action_eventhandlers) + g.game_ehs.values()

        H, M, A = Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA, Identity.TYPE.ADMIN
        idlist = [A, H, H, M, M]
        del H, M, A

        pl = g.players[1:]
        seed = sync_primitive(g.random.getrandbits(32), g.players)
        random.Random(seed).shuffle(pl)
        g.players[1:] = pl
        g.emit_event('reseat', None)

        for p, identity in zip(g.players, idlist):
            p.identity = Identity()
            p.identity.type = identity
            g.process_action(RevealIdentity(p, g.players))

        force_hakurei = BatchList(g.players[1:3])
        force_moriya  = BatchList(g.players[3:5])
        g.forces = BatchList([force_hakurei, force_moriya])

        from . import characters

        g.switch_character(g.players[0], CharChoice(characters.koakuma.Koakuma))
        g.koakuma = koakuma = g.players[0]
        koakuma.tags['books'] = g.total_books
        koakuma.maxlife += 4
        koakuma.life += 4

        # choose girls -->
        chars = characters.get_characters('book')
        try:
            chars.remove(characters.koakuma.Koakuma)
        except:
            pass

        g.random.shuffle(chars)

        testing = list(settings.TESTING_CHARACTERS)
        testing = filter_out(chars, lambda c: c.__name__ in testing)
        chars = g.random.sample(chars, 24)

        if Game.SERVER_SIDE:
            choices = [CharChoice(cls) for cls in chars[-20:]]
        else:
            choices = [CharChoice(None) for _ in xrange(20)]

        del chars[-20:]

        for p in g.players[1:]:
            c = choices[-4:]
            del choices[-4:]
            akari = CharChoice(characters.akari.Akari)
            akari.real_cls = chars.pop()
            c.append(akari)
            c.extend([CharChoice(cls) for cls in testing])
            p.choices = c
            p.reveal(c)

        pl = g.players[1:]
        mapping = {p: p.choices for p in pl}

        with InputTransaction('ChooseGirl', pl, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            rst = user_input(pl, ilet, timeout=30, type='all', trans=trans)

        for p in pl:
            c = rst[p] or p.choices[0]
            g.switch_character(p, c)

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=4))

        pl = g.players
        for i, idx in enumerate(cycle(range(len(pl)))):
            if i >= 6000: break
            p = pl[idx]
            if p.dead:
                g.process_action(PlayerRevive(p, p, 2))
                g.process_action(DrawCards(p, 2))
                continue

            g.emit_event('player_turn', p)
            try:
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass

    def can_leave(g, p):
        return False

    def update_event_handlers(g):
        ehclasses = list(action_eventhandlers) + g.game_ehs.values()
        ehclasses += g.ehclasses
        g.event_handlers = EventHandler.make_list(ehclasses)

    def switch_character(g, p, choice):
        choice.char_cls = choice.real_cls or choice.char_cls  # reveal akari

        g.players.reveal(choice)
        cls = choice.char_cls

        log.info(u'>> NewCharacter: %s %s', Identity.TYPE.rlookup(p.identity.type), cls.__name__)

        # mix char class with player -->
        old = p
        p, oldcls = mixin_character(p, cls)
        g.decorate(p)
        g.players.replace(old, p)
        g.forces[0].replace(old, p)
        g.forces[1].replace(old, p)

        ehs = g.ehclasses
        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()
        g.emit_event('switch_character', p)

        return p

    def decorate(g, p):
        from cards import CardList
        p.cards          = CardList(p, 'cards')       # Cards in hand
        p.showncards     = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')      # Equipments
        p.fatetell       = CardList(p, 'fatetell')    # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')     # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags           = defaultdict(int)
