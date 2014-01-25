# -*- coding: utf-8 -*-

from game.autoenv import GameObject

characters = []
raid_characters = []
id8exclusive_characters = []


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


def _reg_to(l):
    def register(cls):
        l.append(cls)
        Character.character_classes[cls.__name__] = cls
        return cls

    return register


register_character = _reg_to(characters)
register_raid_character = _reg_to(raid_characters)
register_id8exclusive_character = _reg_to(id8exclusive_characters)

register_special_character = _reg_to([])


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
