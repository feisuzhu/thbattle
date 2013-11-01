# -*- coding: utf-8 -*-

from game.autoenv import GameObject

characters = []
ex_characters = []


class Character(GameObject):
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


def register_character(cls):
    characters.append(cls)
    return cls


def register_ex_character(cls):
    ex_characters.append(cls)
    return cls


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
