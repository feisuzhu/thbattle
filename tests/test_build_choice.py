# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from nose.tools import eq_
from utils import ObjectDict, BatchList

# -- own --

# -- code --


class options:
    db = 'sqlite:////dev/shm/thbtest.sqlite3'


class ObjectDict(ObjectDict):
    def __hash__(self):
        return id(self)


class TestFunctions(object):

    @classmethod
    def setUpClass(cls):
        import os
        try:
            os.unlink('/dev/shm/thbtest.sqlite3')
        except:
            pass

        import db.session
        db.session.init('sqlite:////dev/shm/thbtest.sqlite3')

        from game import autoenv
        autoenv.init('Server')

    def testImperialChoice(self):
        from thb.item import ImperialChoice
        from thb.characters.sp_aya import SpAya

        class p:
            class account:
                userid = 1

        pi = {1: ['imperial-choice:SpAya', 'foo']}
        eq_(ImperialChoice.get_chosen(pi, [p]), [(p, SpAya)])

    def testBuildChoices(self):
        import logging
        from thb.common import build_choices
        import random
        from thb.characters.baseclasses import get_characters
        from thb import characters
        from game import autoenv
        # def build_choices(g, items, candidates, players, num, akaris, shared):

        log = logging.getLogger('test')

        g = ObjectDict({
            'players': BatchList([ObjectDict({
                'account': ObjectDict({'userid': i}),
                'reveal': lambda o, i=i: log.info('Reveal to %s: %s', i, o),
            }) for i in xrange(8)]),
            'random': random.Random(12341234),
            'SERVER_SIDE': True,
            'CLIENT_SIDE': False,
        })
        autoenv.Game.getgame = staticmethod(lambda: g)
        chars = get_characters('common', '3v3')
        assert chars

        choices, imperial = build_choices(g, {}, chars, g.players, 10, 3, True)
        eq_(len(choices.items()), len(g.players))
        eq_(len(set([id(i) for i in choices.values()])), 1)
        eq_(set(choices.keys()), set(g.players))
        eq_(imperial, [])

        choices, imperial = build_choices(g, {0: ['imperial-choice:SpAya', 'foo']}, chars, g.players, 10, 3, True)
        eq_(len(choices.items()), len(g.players))
        eq_(len(set([id(i) for i in choices.values()])), 1)
        eq_(set(choices.keys()), set(g.players))
        p, c = imperial[0]
        eq_((p, c.char_cls), (g.players[0], characters.sp_aya.SpAya))
        assert c in choices[p]
        del c
        eq_(sum([c.akari for c in choices[p]]), 3)

        choices, imperial = build_choices(g, {0: ['imperial-choice:SpAya', 'foo']}, chars, g.players, [4] * 8, [1] * 8, False)
        eq_(len(choices.items()), len(g.players))
        eq_(len(set([id(i) for i in choices.values()])), 8)
        eq_(set(choices.keys()), set(g.players))
        eq_([len(i) for i in choices.values()], [4] * 8)
        eq_([len([j for j in i if j.akari]) for i in choices.values()], [1] * 8)

        p, c = imperial[0]
        eq_((p, c.char_cls), (g.players[0], characters.sp_aya.SpAya))
        assert c in choices[p]
