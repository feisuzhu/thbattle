# -*- coding: utf-8 -*-

from game.autoenv import GameObject
from options import options
from collections import defaultdict

# common, id5, id8, raid, raid_ex, faith, kof, 3v3, testing
# -id5, -id8, ...
characters_by_category = defaultdict(set)


class Character(GameObject):
    character_classes = {}

    def __init__(self, player):
        self.player = player

    def get_skills(self, skill):
        return [s for s in self.skills if issubclass(s, skill)]

    has_skill = get_skills

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

register_character = register_character_to('common')


def get_characters(*cats, **kwargs):
    cats = set(cats)
    if '-common' in cats:
        cats.discard('-common')
    else:
        cats.add('common')

    chars = set()
    chars.update(*[characters_by_category[c] for c in cats])
    chars.difference_update(*[characters_by_category['-' + c] for c in cats])
    chars = list(sorted(chars, key=lambda i: i.__name__))
    return chars


def mixin_character(player, char_cls):
    assert issubclass(char_cls, Character)
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
