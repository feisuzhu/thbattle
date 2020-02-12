# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --

# -- code --
class TestStart2v2(object):
    @classmethod
    def setup_class(cls):
        from game import autoenv
        autoenv.init('Server')

    def getInputletInstances(self):
        from thb.thb2v2 import THBattle2v2

        from thb.cards.definition import AttackCard
        from thb.characters.youmu import Youmu
        from thb.common import CharChoice
        from thb.inputlets import ActionInputlet
        from thb.inputlets import ChooseGirlInputlet
        from thb.inputlets import ChooseIndividualCardInputlet
        from thb.inputlets import ChooseOptionInputlet
        from thb.inputlets import ChoosePeerCardInputlet
        from thb.inputlets import ProphetInputlet

        from .mock import ServerWorld
        w = ServerWorld()
        g = w.fullgame(THBattle2v2)
        core = w.core
        boot = core.game.get_bootstrap_action(g)
        players = boot.players

        self.game = g
        p = players[0]
        ch = Youmu(p)

        ilets1 = [
            ChooseGirlInputlet(self, {p: [CharChoice(Youmu)]}),
        ]

        for i in ilets1:
            i.actor = p

        ilets2 = [
            ActionInputlet(self, ['cards', 'showncards'], []),
            ChooseIndividualCardInputlet(self, [AttackCard()]),
            ChooseOptionInputlet(self, (False, True)),
            ChoosePeerCardInputlet(self, ch, ['cards']),
            ProphetInputlet(self, [AttackCard()]),
        ]

        for i in ilets2:
            i.actor = ch

        return g, p, ilets1 + ilets2

    def testParseNone(self):
        g, p, ilets = self.getInputletInstances()
        for ilet in ilets:
            ilet.parse(None)

    def testCallDataWithoutResultBeingSet(self):
        g, p, ilets = self.getInputletInstances()
        for ilet in ilets:
            ilet.data()

    def testInputletNameClash(self):
        from game.base import Inputlet
        classes = Inputlet.__subclasses__()

        clsnames = set([cls.tag() for cls in classes])
        assert len(clsnames) == len(classes)

    def teztChooseOptionInputlet(self):

        from thb.inputlets import ChooseOptionInputlet
        from utils.misc import BatchList

        from .mock import ServerWorld
        w = ServerWorld()
        g = w.fullgame()
        core = w.core
        boot = core.game.get_bootstrap_action(g)
        pl = boot.players

        p = pl[0]
        g.me = p
        p.client._ep.recv.put(['game:data', ['I:ChooseOption:1', True]])
        p.client._ep.recv.put(['game:data', ['I&:ChooseOption:2', False]])
        p.client._ep.recv.put(['game:data', ['I|:ChooseOption:3', True]])

        ilet = ChooseOptionInputlet(self, (False, True))

        assert user_input([p], ilet) is True
        assert user_input([p], ilet, type='all') == {p: False}
        assert user_input([p], ilet, type='any') == (p, True)

        for p in pl:
            assert p.client._ep.send == [
                ['game:data', ['RI:ChooseOption:1', True]],
                ['game:data', ['RI&:ChooseOption:2', False]],
                ['game:data', ['RI|:ChooseOption:3', True]],
            ]

        '''
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

        ilet = ChooseOptionInputlet(self, (False, True))

        eq_(user_input([p], ilet), True)
        eq_(user_input([p], ilet, type='all'), {p: False})
        eq_(user_input([p], ilet, type='any'), (p, True))

    def makeGame(self):
        from game import autoenv

        from thb.thb3v3 import THBattle
        from thb.cards import Deck, CardList
        from thb.characters.eirin import FirstAid, Medic

        from utils import BatchList

        autoenv.init('Server')
        g = THBattle()
        g.IS_DEBUG = True
        g.random = random
        hook_game(g)
        deck = Deck()
        g.deck = deck
        g.action_stack = [autoenv.Action(None, None)]
        g.gr_groups = WeakSet()

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
        from thb.cards import migrate_cards
        from thb.characters.eirin import FirstAid, Medic
        from thb.inputlets import ActionInputlet

        g, p = self.makeGame()
        c1, c2, c3 = g.deck.getcards(3)

        # migrate_cards([c1, c2, c3], p.cards, no_event=True)
        migrate_cards([c1, c2, c3], p.cards)

        ilet = ActionInputlet(self, ['cards', 'showncards'], candidates=g.players)
        ilet.skills = [FirstAid]
        ilet.cards = [c1, c2]
        ilet.players = [p, p]
        ilet.actor = p
        eq_(ilet.data(), [[0], [c1.sync_id, c2.sync_id], [0, 0], {}])

        p.client.gdlist.append([r'>I:Action:\d+', [[], [c1.sync_id, c2.sync_id], [], {}]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[], [c1, c2], [], {}])

        p.client.gdlist.append([r'>I:Action:\d+', [[0], [c2.sync_id, c3.sync_id], [], {}]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[FirstAid], [c2, c3], [], {}])

        p.client.gdlist.append([r'>I:Action:\d+', [[1, 0], [c3.sync_id, c1.sync_id], [0], {}]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), [[Medic, FirstAid], [c3, c1], [], {}])

        p.client.gdlist.append([r'>I:Action:\d+', [[1, 0], [c3.sync_id, c1.sync_id], [0], {}]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], candidates=g.players)
        eq_(user_input([p], ilet), [[Medic, FirstAid], [c3, c1], [p], {}])

        p.client.gdlist.append([r'>I:Action:\d+', [[3, 0], [c3.sync_id, c1.sync_id], [0], {}]])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), None)

        p.client.gdlist.append([r'>I:Action:\d+', 'evil'])
        ilet = ActionInputlet(self, ['cards', 'showncards'], [])
        eq_(user_input([p], ilet), None)

    def testChooseIndividualCardInputlet(self):
        from thb.inputlets import ChooseIndividualCardInputlet

        g, p = self.makeGame()
        cards = g.deck.getcards(5)

        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        ilet.set_card(cards[1])
        eq_(ilet.data(), cards[1].sync_id)

        p.client.gdlist.append([r'>I:ChooseIndividualCard:\d+', cards[2].sync_id])
        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        eq_(user_input([p], ilet), cards[2])

        p.client.gdlist.append([r'>I:ChooseIndividualCard:\d+', 343434])
        ilet = ChooseIndividualCardInputlet(self, cards=cards)
        eq_(user_input([p], ilet), None)

    def testChoosePeerCardInputlet(self):
        from thb.inputlets import ChoosePeerCardInputlet
        from thb.cards import migrate_cards

        g, p = self.makeGame()
        tgt = g.players[1]

        cards = g.deck.getcards(5)
        migrate_cards(cards, tgt.cards)

        showncards = g.deck.getcards(5)
        migrate_cards(showncards, tgt.showncards)

        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        ilet.set_card(cards[1])
        eq_(ilet.data(), cards[1].sync_id)

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', cards[2].sync_id])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), cards[2])

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', showncards[2].sync_id])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), None)

        p.client.gdlist.append([r'>I:ChoosePeerCard:\d+', 343434])
        ilet = ChoosePeerCardInputlet(self, target=tgt, categories=['cards'])
        eq_(user_input([p], ilet), None)

    def testProphetInputlet(self):
        from game import autoenv
        autoenv.init('Server')

        from thb.inputlets import ProphetInputlet

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
        from thb.common import CharChoice
        from thb.characters.youmu import Youmu
        from thb.characters.seiga import Seiga
        from thb.inputlets import ChooseGirlInputlet

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
        from thb.thb3v3 import THBattle  # noqa
        from thb.thbkof import THBattleKOF  # noqa
        from thb.thbidentity import THBattleIdentity  # noqa
    '''
