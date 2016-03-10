# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import OrderedDict, defaultdict
from itertools import cycle
import logging
import random

# -- third party --
# -- own --
from game.autoenv import Game, sync_primitive
from game.base import get_seed_for
from utils import partition
import settings


# -- code --
log = logging.getLogger('thb.common')


class CharChoice(object):
    chosen = False
    akari = False

    def __init__(self, char_cls=None, akari=False):
        self.set(char_cls, akari)

    def __data__(self):
        return self.char_cls.__name__ if not self.akari else 'Akari'

    def sync(self, data):
        from thb.characters.baseclasses import Character
        self.set(Character.character_classes[data], False)

    def conceal(self):
        self.char_cls = None
        self.chosen = False
        self.akari = False

    def set(self, char_cls, akari=False):
        self.char_cls = char_cls

        if akari:
            self.akari = True
            if Game.getgame().CLIENT_SIDE:
                from thb import characters
                self.char_cls = characters.Akari

    def __repr__(self):
        return '<Choice: {}{}>'.format(
            'None' if not self.char_cls else self.char_cls.__name__,
            '[Akari]' if self.akari else '',
        )


class PlayerIdentity(object):
    def __init__(self):
        self._type = self.TYPE.HIDDEN

    def __data__(self):
        return ['identity', self.type]

    def __str__(self):
        return self.TYPE.rlookup(self.type)

    def sync(self, data):
        assert data[0] == 'identity'
        self._type = data[1]

    def is_type(self, t):
        g = Game.getgame()
        pl = g.players
        return sync_primitive(self.type == t, pl)

    def set_type(self, t):
        if Game.SERVER_SIDE:
            self._type = t

    def get_type(self):
        return self._type

    type = property(get_type, set_type)


def roll(g, items):
    from thb.item import European
    roll = range(len(g.players))
    g.random.shuffle(roll)
    pl = g.players
    for i, p in enumerate(pl):
        if European.is_european(g, items, p):
            g.emit_event('european', p)
            roll.remove(i)
            roll.insert(0, i)
            break

    roll = sync_primitive(roll, pl)
    roll = [pl[i] for i in roll]
    g.emit_event('game_roll', roll)
    return roll


def build_choices(g, items, candidates, players, num, akaris, shared):
    from thb.item import ImperialChoice

    candidates = list(candidates)
    seed = get_seed_for(g.players)
    shuffler = random.Random(seed)
    shuffler.shuffle(candidates)

    if shared:
        entities = ['shared']
        num = [num]
        akaris = [akaris]
    else:
        entities = players

    assert len(num) == len(akaris) == len(entities), 'Uneven configuration'
    assert sum(num) <= len(candidates), 'Insufficient choices'

    result = defaultdict(list)

    # ANCHOR(test)
    # ----- testing -----
    testing = set(settings.TESTING_CHARACTERS)
    testing, candidates = partition(lambda c: c.__name__ in testing, candidates)

    entities_for_testing = entities[:]
    shuffler.shuffle(entities_for_testing)
    for e, cls in zip(cycle(entities_for_testing), testing):
        result[e].append(CharChoice(cls))

    # ----- imperial (force chosen by ImperialChoice) -----
    imperial = ImperialChoice.get_chosen(items, players)
    imperial = [(p, CharChoice(cls)) for p, cls in imperial]

    for p, c in imperial:
        result['shared' if shared else p].append(c)

    # ----- normal -----
    for e, n in zip(entities, num):
        for _ in xrange(len(result[e]), n):
            result[e].append(CharChoice(candidates.pop()))

    # ----- akaris -----
    if g.SERVER_SIDE:
        rest = candidates
    else:
        rest = [None] * len(candidates)

    g.random.shuffle(rest)

    for e, n in zip(entities, akaris):
        for i in xrange(-n, 0):
            result[e][i].set(rest.pop(), True)

    # ----- compose final result, reveal, and return -----
    if shared:
        result = OrderedDict([(p, result['shared']) for p in players])
    else:
        result = OrderedDict([(p, result[p]) for p in players])

    for p, l in result.items():
        p.reveal(l)

    return result, imperial
