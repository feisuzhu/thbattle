# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, Action, GameError, GameEnded, PlayerList
from game import TimeLimitExceeded

from actions import *
from itertools import cycle
import random

from utils import BatchList, check, CheckFailed

import logging
log = logging.getLogger('THBattle')

def mixin_character(player, charcls):
    pcls = player.__class__
    clsn1 = pcls.__name__
    clsn2 = charcls.__name__
    new_cls = type('%s_%s' % (clsn1, clsn2), (pcls, charcls), {})
    player.__class__ = new_cls

class CharChoice(object):
    chosen = None
    def __init__(self, char_cls, cid):
        self.char_cls = char_cls
        self.cid = cid

    def __data__(self):
        return dict(
            char_cls=self.char_cls.__name__,
            cid=self.cid,
        )

    def sync(self, data):
        from characters import characters as chars
        for cls in chars:
            if cls.__name__ == data['char_cls']:
                self.char_cls = cls
                break
        else:
            self.char_cls = None

class THBattle(Game):
    name = u'符斗祭 - 3v3 - 休闲'
    n_persons = 1

    # -----BEGIN PLAYER STAGES-----
    NORMAL = 'NORMAL'
    DRAWCARD_STAGE = 'DRAWCARD_STAGE'
    ACTION_STAGE = 'ACTION_STAGE'
    DROPCARD_STAGE = 'DROPCARD_STAGE'
    # -----END PLAYER STAGES-----

    if Game.CLIENT_SIDE:
        # not loading these things on server
        # FIXME: should it be here?
        from ui import THBattleUI as ui_class

    def game_start(self):
        # game started, init state
        from cards import Card, Deck, CardList

        for cls in action_eventhandlers:
            self.event_handlers.append(cls())

        forces = BatchList([PlayerList(), PlayerList()])
        for i, p in enumerate(self.players):
            f = i%2
            p.force = f
            forces[f].append(p)


        # choose girls -->
        from characters import characters as _chars
        # FIXME: this is for debug
        chars = _chars * 8
        if Game.SERVER_SIDE:
            choice = [
                CharChoice(cls, cid)
                for cls, cid in zip(random.sample(chars, 18), xrange(18))
            ]
        elif Game.CLIENT_SIDE:
            choice = [
                CharChoice(None, i)
                for i in xrange(18)
            ]
        fchoice = [
            choice[:9],
            choice[9:],
        ]
        forces[0].reveal(fchoice[0])
        forces[1].reveal(fchoice[1])

        chosen_girls = []
        pl = PlayerList(self.players)
        def process(p, cid):
            try:
                retry = p._retry
            except AttributeError:
                retry = 3

            retry -= 1
            try:
                check(isinstance(cid, int))
                f = p.force
                check(0 <= cid < len(choice))
                c = choice[cid]
                check(c in fchoice[f])
                if c.chosen and retry > 0:
                    p._retry = retry
                    raise ValueError
                c.chosen = p
                chosen_girls.append(c)
                self.emit_event('girl_chosen', c)
                pl.remove(p)
                return c
            except CheckFailed as e:
                import traceback
                traceback.print_exc(e)
                try:
                    del p._retry
                except AttributeError:
                    pass
                return None

        self.players.user_input_all('choose_girl', process, choice, timeout=30)

        # now you can have them.
        forces[1].reveal(fchoice[0])
        forces[0].reveal(fchoice[1])

        # if there's any person didn't make a choice -->
        # FIXME: this can choose girl from the other force!
        if pl:
            choice = [c for c in choice if not c.chosen]
            sample = [
                SyncPrimitive(i)
                for i in random.sample(xrange(len(choice)), len(pl))
            ]
            self.players.reveal(sample)
            sample = [i.value for i in sample]
            for p, i in zip(pl, sample):
                c = choice[i]
                c.chosen = p
                chosen_girls.append(c)
                self.emit_event('girl_chosen', c)

        # mix char class with player -->
        for c in chosen_girls:
            p = c.chosen
            mixin_character(p, c.char_cls)
            p.skills = p.skills[:] # make it instance variable
            for cls in p.eventhandlers_required:
                self.event_handlers.append(cls())

        for p in self.players:
            p.cards = CardList(p, CardList.HANDCARD, []) # Cards in hand
            p.shown_cards = CardList(p, CardList.SHOWNCARD, []) # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, CardList.EQUIPS, []) # Equipments
            p.fatetell = CardList(p, CardList.FATETELL, []) # Cards in the Fatetell Zone

            p.tags = {}

            p.life = p.maxlife
            p.dead = False
            p.stage = self.NORMAL

        self.deck = Deck()

        self.emit_event('simplegame_begin', None)

        try:
            for p in self.players:
                self.process_action(DrawCards(p, amount=4))

            for p in cycle(self.players):
                if not p.dead:
                    self.emit_event('player_turn', p)
                    self.process_action(FatetellStage(target=p))
                    self.process_action(DrawCardStage(target=p))
                    self.process_action(ActionStage(target=p))
                    self.process_action(DropCardStage(target=p))
        except GameEnded:
            pass

    def game_ended(self):
        return all(p.dead or p.dropped for p in self.players)
