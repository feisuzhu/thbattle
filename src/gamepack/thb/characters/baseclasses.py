# -*- coding: utf-8 -*-

from game.autoenv import GameObject

characters = []
raid_characters = []
id8exclusive_characters = []
categories = {
    'all': characters,
    'raid_ex': raid_characters,
    'id8': id8exclusive_characters,
}


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


def register_character_to(cats=(), all=None):
    if all is None:
        if cats and not cats[0].startswith('-'):
            all = False
        else:
            all = True

    if all:
        cats += ('all', )

    lists = [categories.setdefault(c, []) for c in cats]

    def register(cls):
        Character.character_classes[cls.__name__] = cls
        for l in lists:
            l.append(cls)
        return cls

    return register

chars_cache = { }

def get_characters(cats=(), all=True):
    cats = frozenset(cats)
    if all:
        cats |= set(['all'])

    if cats in chars_cache:
        return list(chars_cache[cats])

    chars = set()
    chars.update(*[categories.get(c, []) for c in cats])
    chars.difference_update(*[categories.get('-' + c, []) for c in cats])
    chars=tuple(sorted(chars, key=lambda i: i.__name__))
    chars_cache[cats] = chars
    return list(chars)

register_character = register_character_to(())
register_raid_character = register_character_to(('raid_ex', ))
register_id8exclusive_character = register_character_to(('id8', ))

register_special_character = register_character_to(('special', ))


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
