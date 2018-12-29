# -*- coding: utf-8 -*-

# -- stdlib --
from typing import List, Union

# -- third party --
# -- own --
from client.base import Game
from thb.actions import BaseFatetell, CardMovement
from thb.cards.base import Card, CardList, VirtualCard
from thb.mode import THBattle


# -- code --

# MigrateOpcode:
NOP        = 0  # No operation. never used.
DUP        = 1  # Duplicate top elem
GET        = 2  # Get a CardSprite, find in hand/dropped area. Create if not found. args: Card, create_in return value: CardSprite.
CREATE     = 3  # Create new CardSprite for Card, arg:Card, Area. return CardSprite
MOVE       = 4  # Move CardSprite to another Area. arg: CardSprite, Area, no return value.
FADE       = 5  # Fade CardSprite, arg: CardSprite, no ret val.
GRAY       = 6  # Set CardSprite gray, arg: CardSprite, no ret val.
UNGRAY     = 7  # Unset CardSprite gray, arg: CardSprite, no ret val.
FATETELL   = 8  # Play Fatetell animation, arg: CardSprite, no ret val.
SHOW       = 9
UNSHOW     = 10
AREA_HAND  = 11
AREA_DECK  = 12
AREA_DROP  = 13
AREA_PORT0 = 14
AREA_PORT1 = 15
AREA_PORT2 = 16
AREA_PORT3 = 17
AREA_PORT4 = 18
AREA_PORT5 = 19
AREA_PORT6 = 20
AREA_PORT7 = 21
AREA_PORT8 = 22
AREA_PORT9 = 23


def _dbgprint(ins):
    s = [
        'NOP', 'DUP', 'GET', 'CREATE', 'MOVE', 'FADE', 'GRAY', 'UNGRAY', 'FATETELL',
        'AREA_HAND', 'AREA_DECK', 'AREA_DROP',
        'AREA_PORT0', 'AREA_PORT1', 'AREA_PORT2', 'AREA_PORT3', 'AREA_PORT4',
        'AREA_PORT5', 'AREA_PORT6', 'AREA_PORT7', 'AREA_PORT8', 'AREA_PORT9',
    ]
    rst = []
    for i in ins:
        if isinstance(i, int):
            rst.append(s[i])
        else:
            rst.append(repr(i))

    from UnityEngine import Debug
    Debug.Log(repr(rst))


class THBattleClient(THBattle, Game):
    pass


def card_migration_instructions(g: THBattleClient, args: CardMovement) -> List[Union[int, Card]]:
    act, cards, _from, to, is_bh = args

    ops: List[Union[int, Card]] = []

    if to is None: return ops  # not supposed to have visual effects

    def cl2index(cl: CardList) -> int:
        assert cl.owner
        for i, p in enumerate(g.players):
            if p.player == cl.owner.player:
                return i
        else:
            raise ValueError

    # -- card actions --
    me = g.find_character(g.me)

    if _from is me.showncards and to is not me.showncards:
        tail = [DUP, UNSHOW]
    elif _from is not me.showncards and to is me.showncards:
        tail = [DUP, SHOW]
    else:
        tail = []

    if to.owner is me and to.type in ('cards', 'showncards'):
        tail += [DUP, UNGRAY, AREA_HAND, MOVE]
    else:
        if to.type in ('droppedcard', 'detached'):
            if isinstance(act, BaseFatetell):
                if to.type == 'detached':
                    tail += [DUP, DUP, UNGRAY if act.succeeded else GRAY, FATETELL, AREA_DROP, MOVE]
                else:
                    return []  # no animation
            else:
                gray = to.type == 'droppedcard'
                tail += [DUP, GRAY if gray else UNGRAY, AREA_DROP, MOVE]

        elif to.owner:
            tail += [DUP, DUP, UNGRAY, FADE, AREA_PORT0 + cl2index(to), MOVE]
        else:
            return []  # no animation

    # -- sprites --
    rawcards = [c for c in cards if not c.is_card(VirtualCard)]
    assert _from is not None

    for c in rawcards:
        if _from.type in ('deckcard', 'droppedcard') or not _from.owner:
            ops += [c, AREA_DECK, GET]
        elif _from.owner is me and _from.type in ('cards', 'showncards'):
            ops += [c, AREA_HAND, GET]
        else:
            ops += [c, AREA_PORT0 + cl2index(_from), CREATE]

        ops += tail

    # _dbgprint(ops)
    return ops


def get_display_tags(p):
    from thb.meta.tags import get_display_tags as ui_tags
    return [i[0] for i in ui_tags(p)]
