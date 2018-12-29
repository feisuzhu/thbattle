# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, List, Optional, Sequence, TYPE_CHECKING, Tuple, Type

# -- third party --
# -- own --
from game.base import Game, GameItem, Player
from server.base import Client, Game as ServerGame
from utils.misc import BatchList, exceptions


# -- typing --
if TYPE_CHECKING:
    from thb.characters.base import Character  # noqa: F401
    from thb.thbrole import THBRoleRole  # noqa: F401

# -- code --
@GameItem.register
class ImperialChoice(GameItem):
    key = 'imperial-choice'
    args = [str]

    def __init__(self, char: str):
        if char == 'Akari' or char not in Character.classes:
            raise exceptions.CharacterNotFound

        self.char_cls = Character.classes[char]

    @property
    def title(self):
        return '选将卡（%s）' % self.char_cls.ui_meta.name

    @property
    def description(self):
        return '你可以选择%s出场。2v2模式不可用。' % self.char_cls.ui_meta.name

    def should_usable(self, g: ServerGame, u: Client):
        from thb.thb2v2 import THBattle2v2
        if isinstance(g, THBattle2v2):
            raise exceptions.IncorrectGameMode

        core = g.core
        items = core.item.items_of(g)

        for l in items.values():
            if self.sku in l:
                raise exceptions.ChooseCharacterConflict

    @classmethod
    def get_chosen(cls, items: Dict[Player, List[GameItem]], pl: BatchList[Player]) -> Dict[Player, Type[Character]]:
        chosen: Dict[Player, Type[Character]] = {}

        for p in pl:
            if p not in items:
                continue

            for i in items[p]:
                if not isinstance(i, cls):
                    continue

                chosen[p] = i.char_cls
                break

        return chosen


@GameItem.register
class ImperialRole(GameItem):
    key = 'imperial-role'
    args = [str]

    def __init__(self, role: str):
        if role not in ('attacker', 'accomplice', 'curtain', 'boss'):
            raise exceptions.InvalidIdentity

        self.role = role
        mapping = {
            'attacker':   '城管',
            'boss':       'BOSS',
            'accomplice': '道中',
            'curtain':    '黑幕',
        }
        self.disp_name = mapping[role]

    @property
    def title(self):
        return '身份卡（%s）' % self.disp_name

    @property
    def description(self):
        return '你可以选择%s身份。身份场可用。' % self.disp_name

    def should_usable(self, g: ServerGame, u: Client):
        from thb.thbrole import THBattleRole
        if not isinstance(g, THBattleRole):
            raise exceptions.IncorrectGameMode

        threshold = {
            'attacker': 4,
            'boss': 1,
            'accomplice': 2,
            'curtain': 1,
        }
        core = g.core
        params = core.game.params_of(g)
        if params['double_curtain']:
            threshold['curtain'] += 1
            threshold['attacker'] -= 1

        threshold[self.id] -= 1

        items = core.item.items_of(g)
        uid = core.auth.uid_of(u)
        for _uid, l in items:
            for i in l:
                i = GameItem.from_sku(i)
                if not isinstance(i, self.__class__):
                    continue

                if _uid == uid:
                    raise exceptions.IdentityAlreadyChosen

                assert i.id in threshold

                threshold[i.id] -= 1

        if any(i < 0 for i in threshold.values()):
            raise exceptions.ChooseIdentityConflict

    @classmethod
    def get_chosen(cls, items: Dict[Player, List[GameItem]], pl: Sequence[Player]) -> List[Tuple[Player, THBRoleRole]]:
        from thb.thbrole import THBRoleRole as T

        mapping = {
            'boss':       T.BOSS,
            'attacker':   T.ATTACKER,
            'accomplice': T.ACCOMPLICE,
            'curtain':    T.CURTAIN,
        }

        rst = []
        for p in pl:
            if p not in items:
                continue

            for i in items[p]:
                if not isinstance(i, cls):
                    continue

                rst.append((p, mapping[i.role]))

        return rst


@GameItem.register
class European(GameItem):
    key = 'european'

    title = '欧洲卡'
    description = 'Roll点保证第一。身份场不可用。'

    @classmethod
    def should_usable(cls, g: ServerGame, u: Client):
        from thb.thbrole import THBattleRole
        if isinstance(g, THBattleRole):
            raise exceptions.IncorrectGameMode

        core = g.core
        items = core.item.items_of(g)

        for l in items:
            if isinstance(l, cls):
                raise exceptions.EuropeanConflict

    @classmethod
    def get_european(cls, g: Game, items: Dict[Player, List[GameItem]]) -> Optional[Player]:
        for p, l in items.items():
            for i in l:
                if isinstance(i, cls):
                    return p

        return None
