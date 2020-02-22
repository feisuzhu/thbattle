# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, ClassVar, Dict, Iterable, List, Set, Type

# -- third party --
# -- own --
from game.base import GameObject, Player
from thb.cards.base import CardList, Skill
from thb.meta.typing import CharacterMeta
from thb.mode import THBEventHandler
from utils.misc import partition


# -- code --
# common, id8, faith, kof, 3v3, testing
# -id8, ...
characters_by_category: Dict[str, Set[Type[Character]]] = defaultdict(set)


class Character(GameObject):
    classes: ClassVar[Dict[str, Type[Character]]] = {}

    # ----- Class Variables -----
    ui_meta: ClassVar[CharacterMeta]
    eventhandlers: ClassVar[List[Type[THBEventHandler]]] = ()
    categories: ClassVar[Iterable[str]] = ()
    boss_skills: ClassVar[List[Type[Skill]]] = ()

    skills: List[Type[Skill]] = ()
    maxlife: int = 0

    # ----- Instance Variables -----
    dead: bool
    life: int
    disabled_skills: Dict[str, Set[Type[Skill]]]
    tags: Dict[str, Any]
    cards: CardList
    showncards: CardList
    equips: CardList
    fatetell: CardList
    special: CardList
    showncardlists: List[CardList]
    player: Player

    def __init__(self, player: Player):
        self.player = player
        self.disabled_skills = defaultdict(set)

        cls = self.__class__

        self.skills = list(cls.skills)
        self.maxlife = cls.maxlife
        self.life = cls.maxlife
        self.dead = False

        self.cards          = CardList(self, 'cards')       # Cards in hand
        self.showncards     = CardList(self, 'showncards')  # Cards which are shown to the others, treated as 'Cards in hand'
        self.equips         = CardList(self, 'equips')      # Equipments
        self.fatetell       = CardList(self, 'fatetell')    # Cards in the Fatetell Zone
        self.special        = CardList(self, 'special')     # used on special purpose
        self.showncardlists = [self.showncards, self.fatetell]
        self.tags           = defaultdict(int)

    def get_player(self) -> Player:
        return self.player

    def get_skills(self, skill: Type['Skill']):
        return [s for s in self.skills if issubclass(s, skill)]

    def has_skill(self, skill: Type['Skill']):
        if self.dead:
            return False

        if any(issubclass(skill, s) for l in self.disabled_skills.values() for s in l):
            return False

        return self.get_skills(skill)

    def disable_skill(self, skill: Type['Skill'], reason: str):
        self.disabled_skills[reason].add(skill)

    def reenable_skill(self, reason: str):
        self.disabled_skills.pop(reason, '')

    def reveal(self, obj: Any) -> None:
        self.player.reveal(obj)

    def __repr__(self) -> str:
        return '<Char: {}>'.format(self.__class__.__name__)


def register_character_to(*cats):
    sets = [characters_by_category[c] for c in set(cats)]

    def register(cls: Type[Character]):
        Character.classes[cls.__name__] = cls

        for s in sets:
            s.add(cls)

        cls.categories = cats
        return cls

    return register


def get_characters(*categories):
    cats: Set[str] = set(categories)
    chars: Set[Type[Character]] = set()
    pos, neg = partition(lambda c: not c.startswith('-'), cats)
    chars.update(*[characters_by_category[c] for c in pos])
    chars.difference_update(*[characters_by_category['-' + c] for c in pos])
    chars.difference_update(*[characters_by_category[c.strip('-')] for c in neg])
    return list(sorted(chars, key=lambda i: i.__name__))
