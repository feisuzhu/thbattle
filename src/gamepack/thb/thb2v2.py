# -*- coding: utf-8 -*-

# -- stdlib --
import random
from itertools import cycle
from collections import defaultdict

# -- third party --

# -- own --
from .actions import PlayerDeath, DrawCards, PlayerTurn, RevealIdentity, DeadDropCards, DrawCardStage
from .actions import action_eventhandlers, migrate_cards, MigrateCardsTransaction
from .characters.baseclasses import mixin_character
from .common import PlayerIdentity, get_seed_for, sync_primitive, CharChoice
from .inputlets import ChooseGirlInputlet, ChooseOptionInputlet
from game.autoenv import Game, EventHandler, InterruptActionFlow, user_input, InputTransaction
from utils.misc import Enum, BatchList
import logging

# -- code --
log = logging.getLogger('THBattle2v2')

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
        if evt_type != 'action_after': return act
        if not isinstance(act, PlayerDeath): return act

        g = Game.getgame()

        # see if game ended
        force1, force2 = g.forces
        if all(p.dead or p.dropped for p in force1):
            g.winners = force2[:]
            g.game_end()

        if all(p.dead or p.dropped for p in force2):
            g.winners = force1[:]
            g.game_end()

        return act


@game_eh
class HeritageHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, DeadDropCards): return act

        g = Game.getgame()
        tgt = act.target
        for f in g.forces:
            if tgt in f:
                break
        else:
            assert False, 'WTF?!'

        other = BatchList(f).exclude(tgt)[0]
        if other.dead: return act

        if user_input([other], ChooseOptionInputlet(self, ('inherit', 'draw'))) == 'inherit':
            lists = [tgt.cards, tgt.showncards, tgt.equips]
            lists.extend(tgt.showncardlists)
            with MigrateCardsTransaction() as trans:
                for cl in lists:
                    if not cl: continue
                    cl = list(cl)
                    other.reveal(cl)
                    migrate_cards(cl, other.cards, unwrap=True, trans=trans)

            act.cancelled = True
        else:
            g.process_action(DrawCards(other, 2))

        return act


@game_eh
class ExtraCardHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_before':
            return act

        if not isinstance(act, DrawCardStage):
            return act

        g = Game.getgame()
        if g.draw_extra_card:
            act.amount += 1

        return act


class Identity(PlayerIdentity):
    class TYPE(Enum):
        HIDDEN = 0
        HAKUREI = 1
        MORIYA = 2


class THBattle2v2(Game):
    n_persons    = 4
    game_ehs     = _game_ehs
    game_actions = _game_actions
    params_def   = {
        'random_force':    (True, False),
        'draw_extra_card': (False, True),
    }

    def game_start(g, params):
        # game started, init state
        from cards import Deck

        g.deck = Deck()

        g.ehclasses = ehclasses = list(action_eventhandlers) + g.game_ehs.values()

        if params['random_force']:
            seed = get_seed_for(g.players)
            random.Random(seed).shuffle(g.players)

        g.draw_extra_card = params['draw_extra_card']

        f1 = BatchList()
        f2 = BatchList()
        g.forces = BatchList([f1, f2])

        H, M = Identity.TYPE.HAKUREI, Identity.TYPE.MORIYA
        for p, id, f in zip(g.players, [H, H, M, M], [f1, f1, f2, f2]):
            p.identity = Identity()
            p.identity.type = id
            p.force = f
            f.append(p)

        pl = g.players
        for p in pl:
            g.process_action(RevealIdentity(p, pl))

        # ----- roll ------
        roll = g.random.choice((
            (0, 2, 3, 1), (0, 3, 2, 1),
            (1, 2, 3, 0), (1, 3, 2, 0),
            (2, 0, 1, 3), (2, 1, 0, 3),
            (3, 0, 1, 2), (3, 1, 0, 2),
        ))
        pl = g.players
        roll = sync_primitive(roll, pl)
        roll = [pl[i] for i in roll]
        g.emit_event('game_roll', roll)
        g.players[:] = roll
        g.emit_event('game_roll_result', g.players[0])
        g.emit_event('reseat', None)
        # ----

        # ban / choose girls -->
        from . import characters
        chars = characters.get_characters('2v2')

        seed = get_seed_for(g.players)
        random.Random(seed).shuffle(chars)

        chars = chars[:20]
        choices = [CharChoice(cls) for cls in chars]

        banned = set()
        mapping = {p: choices for p in g.players}
        with InputTransaction('BanGirl', g.players, mapping=mapping) as trans:
            for p in g.players:
                c = user_input([p], ChooseGirlInputlet(g, mapping), timeout=30, trans=trans)
                c = c or [_c for _c in choices if not _c.chosen][0]
                c.chosen = p
                banned.add(c.char_cls)
                trans.notify('girl_chosen', (p, c))

        assert len(banned) == 4
        chars = [_c for _c in chars if _c not in banned]

        g.random.shuffle(chars)

        if Game.CLIENT_SIDE:
            chars = [None] * len(chars)

        for p in g.players:
            p.choices = [CharChoice(cls) for cls in chars[-4:]]
            p.choices[-1].as_akari = True

            del chars[-4:]

            p.reveal(p.choices)

        mapping = {p: p.choices for p in g.players}
        with InputTransaction('ChooseGirl', g.players, mapping=mapping) as trans:
            ilet = ChooseGirlInputlet(g, mapping)

            @ilet.with_post_process
            def process(p, c):
                c = c or p.choices[0]
                trans.notify('girl_chosen', (p, c))
                return c

            rst = user_input(g.players, ilet, timeout=30, type='all', trans=trans)

        # reveal
        for p, c in rst.items():
            c.as_akari = False
            g.players.reveal(c)
            g.set_character(p, c.char_cls)

        g.event_handlers = EventHandler.make_list(ehclasses)

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
            g.process_action(DrawCards(p, amount=4))

        for i, p in enumerate(cycle(pl)):
            if i >= 6000: break
            if not p.dead:
                g.emit_event('player_turn', p)
                try:
                    g.process_action(PlayerTurn(p))
                except InterruptActionFlow:
                    pass

    def can_leave(g, p):
        return getattr(p, 'dead', False)

    def set_character(g, p, cls):
        # mix char class with player -->
        new, old_cls = mixin_character(p, cls)
        g.decorate(new)
        g.players.replace(p, new)
        g.forces[0].replace(p, new)
        g.forces[1].replace(p, new)
        assert not old_cls
        ehs = g.ehclasses
        ehs.extend(cls.eventhandlers_required)
        g.emit_event('switch_character', new)
        return new

    def decorate(g, p):
        from .cards import CardList
        from .characters.baseclasses import Character
        assert isinstance(p, Character)

        p.cards          = CardList(p, 'cards')       # Cards in hand
        p.showncards     = CardList(p, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        p.equips         = CardList(p, 'equips')      # Equipments
        p.fatetell       = CardList(p, 'fatetell')    # Cards in the Fatetell Zone
        p.special        = CardList(p, 'special')     # used on special purpose
        p.showncardlists = [p.showncards, p.fatetell]
        p.tags           = defaultdict(int)
