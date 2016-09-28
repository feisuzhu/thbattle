# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict

# -- third party --
# -- own --
from game.autoenv import Game, GameObject
from utils.misc import partition

# -- code --
# common, id8, faith, kof, 3v3, testing
# -id8, ...
characters_by_category = defaultdict(set)


class Character(GameObject):
    character_classes = {}

    def __init__(self, player):
        self.player = player
        self.disabled_skills = defaultdict(set)

    def get_skills(self, skill):
        return [s for s in self.skills if issubclass(s, skill)]

    def has_skill(self, skill):
        if self.dead:
            return False

        if any(issubclass(skill, s) for l in self.disabled_skills.values() for s in l):
            return False

        return self.get_skills(skill)

    def disable_skill(self, skill, reason):
        self.disabled_skills[reason].add(skill)

    def reenable_skill(self, reason):
        self.disabled_skills.pop(reason, '')

    def __repr__(self):
        return '<Char: {}>'.format(self.__class__.__name__)

    def __getattr__(self, k):
        return getattr(self.player, k)

    def __setattr__(self, k, v):
        GameObject.__setattr__(self, k, v)
        if not k.startswith('__') and k.endswith('__'):
            assert not hasattr(self.player, k)


def register_character_to(*cats):
    sets = [characters_by_category[c] for c in set(cats)]

    def register(cls):
        Character.character_classes[cls.__name__] = cls
        [s.add(cls) for s in sets]
        cls.categories = cats
        return cls

    return register


def get_characters(*cats):
    cats = set(cats)
    chars = set()
    pos, neg = partition(lambda c: not c.startswith('-'), cats)
    chars.update(*[characters_by_category[c] for c in pos])
    chars.difference_update(*[characters_by_category['-' + c] for c in pos])
    chars.difference_update(*[characters_by_category[c.strip('-')] for c in neg])
    chars = list(sorted(chars, key=lambda i: i.__name__))
    return chars


def mixin_character(player, char_cls):
    assert issubclass(char_cls, Character)

    g = Game.getgame()
    player.index = g.get_playerid(player)

    old = None
    if isinstance(player, Character):
        old = player.__class__
        player = player.player

    new = char_cls(player)
    new.skills = list(char_cls.skills)
    new.maxlife = char_cls.maxlife
    new.life = char_cls.maxlife
    new.dead = False
    return new, old
