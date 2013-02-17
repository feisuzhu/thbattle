# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList, InterruptActionFlow

from actions import *
from itertools import cycle
from collections import defaultdict
import random

from utils import BatchList, check, CheckFailed

from .common import *

import logging
log = logging.getLogger('THBattleRaid')

_game_ehs = {}
def game_eh(cls):
    _game_ehs[cls.__name__] = cls
    return cls

_game_actions = {}
def game_action(cls):
    _game_actions[cls.__name__] = cls
    return cls


@game_eh
class DeathHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, BaseDamage):
            tgt = act.target
            if tgt.life > 0: return act
            g = Game.getgame()
            if not g.process_action(TryRevive(tgt, dmgact=act)):
                g.process_action(PlayerDeath(act.source, tgt))
                from .actions import RevealIdentity, DrawCards, DropCards
                g.process_action(RevealIdentity(tgt, g.players))

                if act.source:
                    src = act.source
                    if tgt.identity.type == Identity.TYPE.ATTACKER:
                        g.process_action(DrawCards(src, 3))
                    elif tgt.identity.type == Identity.TYPE.ACCOMPLICE:
                        if src.identity.type == Identity.TYPE.BOSS:
                            if src.cards:
                                g.players.exclude(src).reveal(list(src.cards))
                                g.process_action(DropCards(src, src.cards))
                            if src.showncards: g.process_action(DropCards(src, src.showncards))
                            if src.equips: g.process_action(DropCards(src, src.equips))

                # see if game ended
                T = Identity.TYPE
                def build():
                    deads = defaultdict(list)
                    for p in g.players:
                        if p.dead:
                            deads[p.identity.type].append(p)
                    return deads

                # curtain's win
                if len([p for p in g.players if p.dead]) == len(g.players) - 1:
                    pl = g.players
                    pl.reveal([p.identity for p in g.players])

                    deads = build()
                    if not deads[T.CURTAIN]:
                        g.winners = [p for p in pl if p.identity.type == T.CURTAIN]
                        raise GameEnded

                deads = build()

                # boss & accomplices' win
                if len(deads[T.ATTACKER]) == g.identities.count(T.ATTACKER):
                    if deads[T.CURTAIN]:
                        pl = g.players
                        pl.reveal([p.identity for p in g.players])

                        g.winners = [p for p in pl if p.identity.type in (T.BOSS, T.ACCOMPLICE)]
                        raise GameEnded

                # attackers' win
                if len(deads[T.BOSS]):
                    pl = g.players
                    pl.reveal([p.identity for p in g.players])

                    g.winners = [p for p in pl if p.identity.type == T.ATTACKER]
                    raise GameEnded

                if tgt is g.current_turn:
                    for a in reversed(g.action_stack):
                        if isinstance(a, UserAction):
                            a.interrupt_after_me()

        return act


class CollectFaith(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt = self.target

        g = Game.getgame()
        cards = g.deck.getcards(self.amount)
        g,players.reveal(cards)
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
        
        amount = getattr(src, 'maxfaith', 999) - len(src.faiths)
        amount = min(amount, act.amount)

        g = Game.getgame()
        g,process_action(CollectFaith(src, src, amount))
        return act
        

class Identity(PlayerIdentity):
    # 异变 解决者
    class TYPE:
        HIDDEN = 0
        MUTANT = 1
        ATTACKER = 2


class RequestAction(object):  # for choose_option
    pass


class MutantMorph(GameException):
    pass


class THBattleRaid(Game):
    n_persons = 4
    game_actions = _game_actions

    def game_start(g):
        # game started, init state
        from cards import Card, CardList

        ehclasses = self.ehclasses = []

        for p in g.players:
            p.cards = CardList(p, 'handcard')  # Cards in hand
            p.showncards = CardList(p, 'showncard')  # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips')  # Equipments
            p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
            p.faiths = CardList(p, 'faiths')  # 'faith' cards
            p.special = CardList(p, 'special')  # used on special purpose

            p.showncardlists = [p.showncards, p.faiths, p.fatetell]  # cardlists should shown to others

            p.tags = defaultdict(int)

            p.dead = False
            p.need_shuffle = False

        # reveal identities
        mutant = g.mutant = g.players[0]
        attackers = g.attackers = g.players[1:]

        mutant.identity = Identity()
        mutant.identity.type = Identity.TYPE.MUTANT

        g.process_action(RevealIdentity(mutant, g.players))

        for p in attackers:
            p.identity = Identity()
            p.identity.type = Identity.TYPE.ATTACKER

            g.process_action(RevealIdentity(p, g.players))

        # choose girl init
        chosen_girls = []
        pl = PlayerList(g.players)
        def process(p, cid):
            try:
                check(isinstance(cid, int))
                i = p._choose_tag
                check(0 <= cid < len(choice) - 1)
                c = choice[cid]
                if c.chosen:
                    raise ValueError
                c.chosen = p
                chosen_girls.append(c)
                g.emit_event('girl_chosen', c)
                pl.remove(p)
                return c

            except CheckFailed:
                return None

        # mutant's choose
        from characters import ex_characters as ex_chars

        choice = [CharChoice(cls, cid) for cid, cls in enumerate(ex_chars)]

        g.emit_event('choose_girl_begin', ([mutant], choice))
        PlayerList([mutant]).user_input_all('choose_girl', process, choice, timeout=15)

        if not chosen_girls:
            # didn't choose
            c = choice[0]
            c.chosen = mutant
            g.emit_event('girl_chosen', c)
            pl.remove(mutant)
        else:
            c = chosen_girls.pop()

        assert c.chosen is mutant

        # mix it in advance
        # so the others could see it

        mixin_character(mutant, c.char_cls)
        mutant.skills = mutant.skills[:]  # make it instance variable
        ehclasses.extend(mutant.eventhandlers_required)

        mutant.life = mutant.maxlife

        g.emit_event('choose_girl_end', None)

        # init deck & mutant's initial equip
        # (SinsackCard, SPADE, 1)
        # (SinsackCard, HEART, Q)
        from cards import Deck, SinsackCard, card_definition
        raid_carddef = [
            carddef for carddef in card_definition
            if carddef[0] is not SinsackCard
        ]

        for carddef in mutant.initial_equips:
            try:
                raid_carddef.remove(carddef)
            except ValueError:
                pass

        g.deck = Deck(raid_carddef)
        deckcards = g.deck.cards

        equips = [
            cls(suit, num, deckcards)
            for cls, suit, num in mutant.initial_equips
        ]
        deckcards.extend(equips)

        migrate_cards(equips, mutant.cards)

        for c in equips:
            act = WearEquipmentAction(mutant, mutant)
            act.associated_card = c
            g.process_action(act)
            
        # attackers' choose
        from characters import characters as chars

        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid) for cid, cls in
                enumerate(random.sample(chars, 16))
            ]

        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(16)
            ]

        # -----------

        g.players.reveal(choice)
        g.emit_event('choose_girl_begin', (attackers, choice))
        attackers.user_input_all('choose_girl', process, choice, timeout=30)
        g.emit_event('choose_girl_end', None)

        # if there's any person didn't make a choice -->
        if pl:
            choice = [c for c in choice if not c.chosen]
            sample = sync_primitive(
                random.sample(xrange(len(choice)), len(pl)), g.players
            )
            for p, i in zip(pl, sample):
                c = choice[i]
                c.chosen = p
                chosen_girls.append(c)
                g.emit_event('girl_chosen', c)

        # mix char class with player -->
        for c in chosen_girls:
            p = c.chosen
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:]  # make it instance variable
            p.life = p.maxlife
            ehclasses.extend(p.eventhandlers_required)

        g.update_event_handlers()

        g.emit_event('game_begin', g)

        try:
            g.process_action(DrawCards(mutant, amount=6))
            for p in attackers:
                g.process_action(DrawCards(p, amount=4))

            # stage 1
            try:
                for i in xrange(500):
                    g.emit_event('round_start', None)
                    for p in attackers:
                        p.tags['action'] = True

                    while True:
                        avail = PlayerList([p for p in attackers if p.tags['action']])
                        if not avail:
                            break

                        p, _ = avail.user_input_any(
                            tag='choose_option',
                            expects=lambda p, data: bool(data),
                            attachment=RequestAction,
                            timeout=15,
                        )

                        p = p or avail[0]

                        p.tags['action'] = False
                        try:
                            g.process_action(PlayerTurn(p))
                        except InterruptActionFlow:
                            pass

                        try:
                            g.process_action(PlayerTurn(mutant))
                        except InterruptActionFlow:
                            pass

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

            mutant.skills.extend(stage2,skills)

            ehclasses = self.ehclasses
            for s in stage1.eventhandlers_required:
                try:
                    ehclasses.remove(s)
                except ValueError:
                    pass

            ehclasses.extend(stage2.eventhandlers_required)

            mutant.maxlife -= stage1.maxlife // 2

            mixin_character(mutant, stage2)

            g.emit_event('mutant_morph', None)

            # stage 2
            for i in xrange(500):
                g.emit_event('round_start', None)
                for p in attackers:
                    p.tags['action'] = True

                try:
                    g.process_action(PlayerTurn(mutant))
                except InterruptActionFlow:
                    pass

                while True:
                    avail = PlayerList([p for p in attackers if p.tags['action']])
                    if not avail:
                        break

                    p, _ = avail.user_input_any(
                        tag='choose_option',
                        expects=lambda p, data: bool(data),
                        attachment=RequestAction,
                        timeout=15,
                    )

                    p = p or avail[0]

                    p.tags['action'] = False
                    try:
                        g.process_action(PlayerTurn(p))
                    except InterruptActionFlow:
                        pass

        except GameEnded:
            pass

    def can_leave(self, p):
        return getattr(p, 'dead', False)

    def update_event_handlers(self):
        ehclasses = list(action_eventhandlers) + self.game_ehs.values()
        ehclasses += self.ehclasses
        self.event_handlers = EventHandler.make_list(ehclasses)
