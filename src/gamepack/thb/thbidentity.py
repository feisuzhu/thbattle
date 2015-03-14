# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, InterruptActionFlow, get_seed_for
from game.autoenv import user_input
from gamepack.thb.actions import DistributeCards, DrawCards, DropCards, PlayerDeath, PlayerTurn
from gamepack.thb.actions import RevealIdentity, action_eventhandlers
from gamepack.thb.characters.baseclasses import mixin_character
from gamepack.thb.common import CharChoice, PlayerIdentity, sync_primitive
from gamepack.thb.inputlets import ChooseGirlInputlet
from utils import Enum, filter_out
import settings


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


class Identity(PlayerIdentity):
    # 城管 BOSS 道中 黑幕
    class TYPE(Enum):
        HIDDEN = 0
        ATTACKER = 1
        BOSS = 4
        ACCOMPLICE = 2
        CURTAIN = 3


class THBattleIdentity(Game):
    n_persons = 8
    game_ehs = _game_ehs
    character_categories = ('id', 'id8')
    params_def = {
        'double_curtain': (False, True),
    }
    T = Identity.TYPE
    identities = [
        T.ATTACKER, T.ATTACKER, T.ATTACKER, T.ATTACKER,
        T.ACCOMPLICE, T.ACCOMPLICE,
        T.CURTAIN,
    ]
    del T

    def game_start(g, params):
        # game started, init state
        from cards import Deck

        g.deck = Deck()
        g.ehclasses = []

        g.double_curtain = params['double_curtain']

        if g.double_curtain:
            g.identities = g.identities[1:] + g.identities[-1:]

        # choose girls init -->
        from .characters import get_characters
        chars = get_characters(*g.character_categories)
        from .characters.akari import Akari

        # ANCHOR(test)
        testing = list(settings.TESTING_CHARACTERS)
        testing = filter_out(chars, lambda c: c.__name__ in testing)

        def choosed(char):
            try:
                chars.remove(char)
            except:
                pass

            try:
                testing.remove(char)
            except:
                pass

        def random_char():
            return g.random.choice(testing + chars)

        # choose boss
        candidates = g.random.sample(chars, 4)
        candidates.extend(testing)

        if Game.CLIENT_SIDE:
            candidates = [None] * len(candidates)

        idx = sync_primitive(g.random.randrange(len(g.players)), g.players)
        boss = g.boss = g.players[idx]

        boss.identity = Identity()
        boss.identity.type = Identity.TYPE.BOSS

        g.process_action(RevealIdentity(boss, g.players))

        boss.choices = [CharChoice(c) for c in candidates]
        boss.choices.append(CharChoice(Akari))
        boss.reveal(boss.choices)

        mapping = {boss: boss.choices}
        with InputTransaction('ChooseGirl', [boss], mapping=mapping) as trans:
            c = user_input([boss], ChooseGirlInputlet(g, mapping), 30, 'single', trans)

            c = c or boss.choices[-1]
            c.chosen = boss
            g.players.reveal(c)
            trans.notify('girl_chosen', (boss, c))

            if c.char_cls is Akari:
                c = CharChoice(random_char())
                g.players.reveal(c)

            choosed(c.char_cls)

            # mix it in advance
            # so the others could see it

            boss = g.switch_character(boss, c.char_cls)

            # boss's hp bonus
            if g.n_persons > 5:
                boss.maxlife += 1

            boss.life = boss.maxlife

        # reseat
        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(g.players)
        g.emit_event('reseat', None)

        # tell the others their own identity
        il = list(g.identities)
        g.random.shuffle(il)
        for p in g.players.exclude(boss):
            p.identity = Identity()
            id = il.pop()
            if Game.SERVER_SIDE:
                p.identity.type = id
            g.process_action(RevealIdentity(p, p))

        # others choose girls
        pl = g.players.exclude(boss)

        candidates = g.random.sample(chars, 3*len(pl) - len(testing))
        candidates.extend(testing)
        g.random.shuffle(candidates)

        if Game.CLIENT_SIDE:
            candidates = [None] * len(candidates)

        del c
        for p in pl:
            p.choices = [CharChoice(c) for c in candidates[:3]]
            p.choices.append(CharChoice(Akari))
            p.reveal(p.choices)
            del candidates[:3]

        mapping = {p: p.choices for p in pl}  # CAUTION, DICT HERE
        with InputTransaction('ChooseGirl', pl, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)
            ilet.with_post_process(lambda p, rst: trans.notify('girl_chosen', (p, rst)) or rst)
            result = user_input(pl, ilet, type='all', trans=trans)

        # not enough chars for random, reuse unselected
        for p in pl:
            if result[p]:
                result[p].chosen = p
                choosed(result[p].char_cls)

        # mix char class with player -->
        for p in pl:
            c = result[p]
            c = c or p.choices[-1]
            g.players.reveal(c)

            if c.char_cls is Akari:
                c = CharChoice(random_char())
                g.players.reveal(c)

            choosed(c.char_cls)
            p = g.switch_character(p, c.char_cls)

        g.emit_event('game_begin', g)

        for p in g.players:
            g.process_action(DistributeCards(p, amount=4))

        pl = g.players.rotate_to(boss)

        for i, p in enumerate(cycle(pl)):
            if i >= 6000: break
            if not p.dead:
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

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
        from cards import CardList
        p.cards          = CardList(p, 'cards')        # Cards in hand
        p.showncards     = CardList(p, 'showncards')   # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')       # Equipments
        p.fatetell       = CardList(p, 'fatetell')     # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')      # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]  # cardlists should shown to others
        p.tags           = defaultdict(int)
