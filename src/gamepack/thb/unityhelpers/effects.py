# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb.actions import BaseFatetell
from gamepack.thb.cards import VirtualCard


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


def card_migration_instructions(g, args):
    act, cards, _from, to = args

    ops = []

    if to is None: return ops  # not supposed to have visual effects

    def _(cl):
        for i, p in enumerate(g.players):
            if p.player == cl.owner.player:
                return i
        else:
            raise ValueError

    # -- card actions --
    if _from is g.me.showncards and to is not g.me.showncards:
        tail = [DUP, UNSHOW]
    elif _from is not g.me.showncards and to is g.me.showncards:
        tail = [DUP, SHOW]
    else:
        tail = []

    if to.owner is g.me and to.type in ('cards', 'showncards'):
        tail += [DUP, UNGRAY, AREA_HAND, MOVE]
    else:
        if to.type in ('droppedcard', 'disputed'):
            if isinstance(act, BaseFatetell):
                if _from.type != 'disputed':
                    tail += [DUP, DUP, UNGRAY if act.succeeded else GRAY, FATETELL, AREA_DROP, MOVE]
                else:
                    return []  # no animation
            else:
                gray = to.type == 'droppedcard'
                tail += [DUP, GRAY if gray else UNGRAY, AREA_DROP, MOVE]

        elif to.owner:
            tail += [DUP, DUP, UNGRAY, FADE, AREA_PORT0 + _(to), MOVE]
        else:
            return []  # no animation

    # -- sprites --
    rawcards = [c for c in cards if not c.is_card(VirtualCard)]

    for c in rawcards:
        if _from.type in ('deckcard', 'droppedcard', 'disputed') or not _from.owner:
            ops += [c, AREA_DECK, GET]
        elif _from.owner is g.me and _from.type in ('cards', 'showncards'):
            ops += [c, AREA_HAND, GET]
        else:
            ops += [c, AREA_PORT0 + _(_from), CREATE]

        ops += tail

    # _dbgprint(ops)
    return ops


def get_display_tags(p):
    from gamepack.thb.ui.ui_meta.tags import tags as tags_meta

    rst = []

    try:
        for t in list(p.tags):
            meta = tags_meta.get(t)
            if meta and meta.display(p, p.tags[t]):
                rst.append(meta.tag_anim(p))

        for c in list(p.fatetell):
            rst.append(c.ui_meta.tag_anim(c))
    except AttributeError:
        pass

    return rst
