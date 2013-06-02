# -*- coding: utf-8 -*-
from collections import defaultdict
from .mock import create_mock_player, hook_game, MockConnection
from nose.tools import eq_
import random


class TestInputlet(object):
    def getInputletInstances(self):
        from gamepack.thb.cards import AttackCard
        from gamepack.thb.characters.youmu import Youmu
        from gamepack.thb.common import CharChoice
        from gamepack.thb.inputlets import ActionInputlet
        from gamepack.thb.inputlets import ChooseGirlInputlet
        from gamepack.thb.inputlets import ChooseIndividualCardInputlet
        from gamepack.thb.inputlets import ChooseOptionInputlet
        from gamepack.thb.inputlets import ChoosePeerCardInputlet
        from gamepack.thb.inputlets import ProphetInputlet

        g, p = self.makeGame()

        ilets = [
            ActionInputlet(self, ['cards', 'showncards'], []),
            ChooseGirlInputlet(self, {p: [CharChoice(Youmu)]}),
            ChooseIndividualCardInputlet(self, [AttackCard()]),
            ChooseOptionInputlet(self),
            ChoosePeerCardInputlet(self, p, ['cards']),
            ProphetInputlet(self, [AttackCard()]),
        ]

        for i in ilets:
            i.actor = p

        return g, p, ilets

    def testParseNone(self):
        g, p, ilets = self.getInputletInstances()
        for ilet in ilets:
            ilet.parse(None)

    def testCallDataWithoutResultBeingSet(self):
        g, p, ilets = self.getInputletInstances()
        for ilet in ilets:
            ilet.data()

    def testInputletNameClash(self):
        from game import Inputlet
        classes = Inputlet.__subclasses__()

        clsnames = set([cls.tag() for cls in classes])
        assert len(clsnames) == len(classes)

    def testChooseOptionInputlet(self):
        from game import autoenv
        from game.autoenv import user_input
        from client.core import TheChosenOne, PeerPlayer

        from gamepack.thb.thb3v3 import THBattle
        from gamepack.thb.inputlets import ChooseOptionInputlet
        from utils import BatchList

        autoenv.init('Server')
        g = THBattle()
        g.IS_DEBUG = True
        pl = [create_mock_player([]) for i in xrange(6)]
        p = pl[0]
        g.me = p
        p.client.gdlist.extend([
            ['I:ChooseOption:1', True],
            ['I&:ChooseOption:2', False],
            ['I|:ChooseOption:3', True],
        ])
        p.client.gdevent.set()
        g.players = BatchList(pl)
        hook_game(g)

        ilet = ChooseOptionInputlet(self)

        eq_(user_input([p], ilet), True)
        eq_(user_input([p], ilet, type='all'), {p: False})
        eq_(user_input([p], ilet, type='any'), (p, True))

        for p in pl:
            eq_(p.client.gdhistory, [
                ['RI:ChooseOption:1', True],
                ['RI&:ChooseOption:2', False],
                ['RI|:ChooseOption:3', True],
            ])

        autoenv.init('Client')
        g = THBattle()
        pl = [PeerPlayer() for i in xrange(6)]
        svr = MockConnection([
            ['RI:ChooseOption:1', True],
            ['RI&:ChooseOption:2', False],
            ['RI|:ChooseOption:3', True],
        ])
        p = TheChosenOne(svr)
        pl[0] = p
        g.me = p
        svr.gdevent.set()
        g.players = BatchList(pl)
        hook_game(g)
        assert autoenv.Game.getgame() is g

        ilet = ChooseOptionInputlet(self)

        eq_(user_input([p], ilet), True)
        eq_(user_input([p], ilet, type='all'), {p: False})
        eq_(user_input([p], ilet, type='any'), (p, True))

    def makeGame(self):
        from game import autoenv

        from gamepack.thb.thb3v3 import THBattle
        from gamepack.thb.cards import Deck, CardList
        from gamepack.thb.characters.eirin import FirstAid, Medic

        from utils import BatchList

        autoenv.init('Server')
        g = THBattle()
        g.IS_DEBUG = True
        g.random = random
        hook_game(g)
        deck = Deck()
        g.deck = deck

        pl = [create_mock_player([]) for i in xrange(6)]
        for p in pl:
            p.skills = [FirstAid, Medic]

            p.cards = CardList(p, 'cards')  # Cards in hand
            p.showncards = CardList(p, 'showncard')  # Cards which are shown to the others, treated as 'Cards in hand'
            p.equips = CardList(p, 'equips')  # Equipments
            p.fatetell = CardList(p, 'fatetell')  # Cards in the Fatetell Zone
            p.faiths = CardList(p, 'faiths')  # Cards in the Fatetell Zone
            p.special = CardList(p, 'special')  # used on special purpose

            p.showncardlists = [p.showncards, p.fatetell]

            p.tags = defaultdict(int)

            p.dead = False

        p = pl[0]
        p.client.gdevent.set()
        g.players = BatchList(pl)

        return g, p

    def testActionInputlet(self):
        from game.autoenv import user_input
        from gamepack.thb.cards import migrate_cards
        from gamepack.thb.characters.eirin import FirstAid, Medic
        from gamepack.thb.inputlets import ActionInputlet

        g, p = self.makeGame()
        c1, c2, c3 = g.deck.getcards(3)

        migrate_cards([c1, c2, c3], p.cards, no_event=True)

        ilet = ActionInputlet(self, ['cards', 'showncards'], candidates=g.players)
        ilet.skills = [FirstAid]
        ilet.cards = [c1, c2]
        ilet.players = [p, p]
        ilet.actor = p
        eq_(ilet.data(), [[0], [c1.syncid, c2.syncid], [0, 0]])

        p.client.gdlist.append([r'>I:Action:\d+', [[], [c1.syncid, c2.syncid], []]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[], [c1, c2], []])

        p.client.gdlist.append([r'>I:Action:\d+', [[0], [c2.syncid, c3.syncid], []]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[FirstAid], [c2, c3], []])

        p.client.gdlist.append([r'>I:Action:\d+', [[1, 0], [c3.syncid, c1.syncid], [0]]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[Medic, FirstAid], [c3, c1], []])

        p.client.gdlist.append([r'>I:Action:\d+', [[1, 0], [c3.syncid, c1.syncid], [0]]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], candidates=g.players)
        eq_(user_input([p], ilet), [[Medic, FirstAid], [c3, c1], [p]])

        p.client.gdlist.append([r'>I:Action:\d+', [[3, 0], [c3.syncid, c1.syncid], [0]]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), None)

        p.client.gdlist.append([r'>I:Action:\d+', 'evil'])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), None)

    def testChooseIndividualCardInputlet(self):
        from game.autoenv import user_input
        from gamepack.thb.inputlets import ChooseIndividualCardInputlet

        g, p = self.makeGame()
        cards = g.deck.getcards(5)

        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        ilet.set_card(cards[1])
        eq_(ilet.data(), cards[1].syncid)

        p.client.gdlist.append([r'>I:ChooseIndividualCard:\d+', cards[2].syncid])
        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        eq_(user_input([p], ilet), cards[2])

        p.client.gdlist.append([r'>I:ChooseIndividualCard:\d+', 343434])
        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        eq_(user_input([p], ilet), None)

    def testChoosePeerCardInputlet(self):
        from game.autoenv import user_input
        from gamepack.thb.inputlets import ChoosePeerCardInputlet
        from gamepack.thb.cards import migrate_cards

        g, p = self.makeGame()
        tgt = g.players[1]

        cards = g.deck.getcards(5)
        migrate_cards(cards, tgt.cards, no_event=True)

        showncards = g.deck.getcards(5)
        migrate_cards(showncards, tgt.showncards, no_event=True)

        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        ilet.set_card(cards[1])
        eq_(ilet.data(), cards[1].syncid)

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', cards[2].syncid])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), cards[2])

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', showncards[2].syncid])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), None)

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', 343434])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), None)

    def testProphetInputlet(self):
        from game import autoenv
        autoenv.init('Server')

        from game.autoenv import user_input
        from gamepack.thb.inputlets import ProphetInputlet

        g, p = self.makeGame()

        cards = g.deck.getcards(5)
        c0, c1, c2, c3, c4 = cards

        ilet = ProphetInputlet(self, cards=cards)
        ilet.set_result([c2, c3, c1], [c0, c4])
        eq_(ilet.data(), [[2, 3, 1], [0, 4]])

        p.client.gdlist.append([r'>I:Prophet:\d+', [[2, 3, 1], [0, 4]]])
        ilet = ProphetInputlet(self, cards=cards)
        eq_(user_input([p], ilet), [[c2, c3, c1], [c0, c4]])

        p.client.gdlist.append([r'>I:Prophet:\d+', [[2, 3], [0, 4]]])
        ilet = ProphetInputlet(self, cards=cards)
        eq_(user_input([p], ilet), [cards, []])

        p.client.gdlist.append([r'>I:Prophet:\d+', [[2, 3, 1, 0], [0, 4]]])
        ilet = ProphetInputlet(self, cards=cards)
        eq_(user_input([p], ilet), [cards, []])

        p.client.gdlist.append([r'>I:Prophet:\d+', [[2, 3, 0], [0, 4]]])
        ilet = ProphetInputlet(self, cards=cards)
        eq_(user_input([p], ilet), [cards, []])

    def testChooseGirlInputlet(self):
        from game.autoenv import user_input
        from gamepack.thb.common import CharChoice
        from gamepack.thb.characters.youmu import Youmu
        from gamepack.thb.characters.seiga import Seiga
        from gamepack.thb.inputlets import ChooseGirlInputlet

        g, p = self.makeGame()
        choices = [CharChoice(Youmu), CharChoice(Seiga)]
        mapping = {p: choices}

        ilet = ChooseGirlInputlet(self, mapping)
        ilet.actor = p
        ilet.set_choice(choices[0])
        eq_(ilet.data(), 0)

        p.client.gdlist.append([r'>I:ChooseGirl:\d+', 0])
        ilet = ChooseGirlInputlet(self, mapping)
        eq_(user_input([p], ilet), choices[0])

    def testGameImport(self):
        from gamepack.thb.thb3v3 import THBattle  # noqa
        from gamepack.thb.thbkof import THBattleKOF  # noqa
        from gamepack.thb.thbidentity import THBattleIdentity  # noqa
        from gamepack.thb.thbraid import THBattleRaid  # noqa
