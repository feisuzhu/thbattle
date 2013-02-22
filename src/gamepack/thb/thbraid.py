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
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseDamage): return act

        tgt = act.target
        if tgt.life > 0: return act
        g = Game.getgame()
        if g.process_action(TryRevive(tgt, dmgact=act)):
            return act

        g.process_action(PlayerDeath(act.source, tgt))
        from .actions import DrawCards, DropCards

        # attackers' win
        if tgt is g.mutant:
            g.winners = g.attackers
            raise GameEnded

        # mutant's win
        if all(p.dead for p in g.attackers):
            g.winners = [g.mutant]
            raise GameEnded

        if tgt in g.attackers:
            for p in [p for p in g.attackers if not p.dead]:
                if p.user_input('choose_option', self):
                    g.process_action(DrawCards(p, 1))

        if tgt is g.current_turn:
            for a in reversed(g.action_stack):
                if isinstance(a, UserAction):
                    a.interrupt_after_me()

        return act


def use_faith(target, amount=1):
    g = Game.getgame()
    assert amount <= len(target.faiths)
    if len(target.faiths) == amount:
        g.process_action(DropCards(target, target.faiths))
        return

    for i in xrange(1, amount + 1):
        c = choose_individual_card(target, target.faiths)
        if not c: break
        g.process_action(DropCards(target, [c]))

    rest = amount - i
    if rest:
        g.process_action(DropCards(target, target.faiths[:rest])


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


class CooperationAction(UserAction):
    no_reveal = True
    def apply_action(self):
        src = self.source
        tgt = self.target

        src.tags['cooperation_tag'] = src.tags['turn_count']
        self.ncards = len(self.associated_cards)

        cards, showncards = partition(
            lambda c: c in src.cards, self.associated_cards
        )
        migrate_cards(cards, tgt.cards)
        migrate_cards(showncards, tgt.showncards)

        returned = user_choose_cards(self, tgt)
        cards, showncards = partition(lambda c: c in tgt.cards, returned)
        migrate_cards(cards, src.cards)
        migrate_cards(showncards, src.showncards)

        src.need_shuffle = True
        tgt.need_shuffle = True

        return True

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['cooperation_tag']

    def cond(self, cl):
        if not len(cl) = self.ncards: return False


class Cooperation(Skill):
    associated_action = CooperationAction
    no_reveal = True

    def target(self, g, src, tl):
        attackers = g.attackers
        tl = [p for p in tl if not p.dead and p in attackers]
        return (tl[-1:], bool(len(tl)))

    def check(self):
        cl = self.associated_cards
        if not cl: return False
        return all(c.resides_in and c.resides_in.type in (
            'handcard', 'showncard',
        ) for c in cl)
       

class Protection(Skill):
    associate_action = None
    target = t_None


class ProtectionAction(GenericAction):
    def __init__(self, source, dmgact):
        self.source = source
        self.target = dmgact.target
        self.dmgact = dmgact

    def apply_action(self):
        use_faith(self.source, 1)
        self.dmgact.target = self.source
        return True


@game_eh
class ProtectionHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstace(act, Damage): return act
        tgt = act.target
        pl = g.attackers[:]
        if tgt not in pl: return act
        if tgt.life != min([p.life for p in pl if not p.dead]): return act

        g = Game.getgame()
        pl.remove(tgt)

        pl = [p for p in pl if not p.dead and len(p.faiths)]
        for p in pl:
            if p.user_input('choose_option', self):
                g.process_action(ProtectionAction(p, act))
                break

        return act
        

class Parry(Skill):
    associate_action = None
    target = t_None


class ParryAction(GenericAction):
    def __init__(self, source, dmgact):
        self.source = source
        self.target = dmgact.target
        self.dmgact = dmgact

    def apply_action(self):
        use_faith(self.source, 1)
        self.dmgact.amount -= 1
        return True


class ParryHandler(EventHandler):
    execute_before = ('ProtectionHandler', )
    def handle(self, evt_type, act):
        if evt_type != 'action_before': return act
        if not isinstance(act, Damage): return act
        tgt = act.target
        if not act.faiths: return act
        if not (act.amount >= 2 or tgt.life <= act.amount): return act

        if not tgt.user_input('choose_option', self): return act

        g = Game.getgame()
        g.process_action(ParryAction(tgt, act))

        return act


class OneUpAction(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        g = Game.getgame()
        assert tgt.dead, 'WTF?!'
        assert tgt in g.attackers

        use_faith(src, 3)

        tgt.dead = False
        tgt.maxlife = tgt.__class__.maxlife
        tgt.life = min(tgt.maxlife, 3)
        tgt.tags['action'] = True

        tgt.skills.remove(OneUp)
        
        return True


class OneUp(Skill):
    associate_action = OneUpAction
    def target(self, g, src, tl):
        attackers = g.attackers
        tl = [p for p in tl if p.dead and p in attackers]
        return (tl[-1:], bool(len(tl)))

    def check(self):
        if len(self.player.faiths) < 3: return False
        return not self.associated_cards

        
class FaithExchange(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        for i in xrange(len(tgt.faiths)):
            c = choose_individual_card(tgt, tgt.faiths)
            if not c: break
            migrate_cards([c], tgt.showncards)

        self.amount = i

        cards = user_choose_cards(self, tgt)
        if not cards:
            cards = tgt.showncards[:self.amount]
        
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
    class TYPE:
        HIDDEN = 0
        MUTANT = 1
        ATTACKER = 2


class RaidLaunchCard(LaunchCard):
    def calc_base_distance(self):
        g = Game.getgame()
        return { p: 1 for p in g.players if not p.dead }


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

        self.action_types[LaunchCard] = RaidLaunchCard

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
                        avail = PlayerList([p for p in attackers if p.tags['action'] and not p.dead])
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
            mutant.life = min(mutant.life, mutant.maxlife)

            mixin_character(mutant, stage2)

            for p in attackers:
                g.process_action(CollectFaith(p, 1))

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
                    avail = PlayerList([p for p in attackers if p.tags['action'] and not p.dead])
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
        return False

    def update_event_handlers(self):
        ehclasses = list(action_eventhandlers) + self.game_ehs.values()
        ehclasses += self.ehclasses
        self.event_handlers = EventHandler.make_list(ehclasses)
