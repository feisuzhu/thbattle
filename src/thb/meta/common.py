# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, Sequence, TYPE_CHECKING

# -- third party --
# -- own --
from game.base import GameViralContext

# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import Card  # noqa: F401
    from thb.mode import THBattle  # noqa: F401


# -- code --
UI_META: Dict[type, Any] = {}


class UIMetaAccessor(object):
    def __init__(self, cls):
        self.for_cls = cls
        self.mro = cls.mro()

    def __getattr__(self, name):
        for cls in self.mro:
            if cls not in UI_META:
                continue

            obj = UI_META[cls]()
            try:
                val = getattr(obj, name)
                return val
            except AttributeError:
                pass

        raise AttributeError(f'{self.for_cls.__name__}.{name}')


def ui_meta(for_cls: type):
    def decorate(cls: type):
        name = for_cls.__name__
        if name in UI_META:
            raise Exception(f'{name} ui_meta redefinition!')

        if cls.__base__ is object:
            cls = type(cls.__name__, (cls, UIMetaBase), {})

        # Type info is handled by plugin
        for_cls.ui_meta = UIMetaAccessor(for_cls)  # type: ignore
        UI_META[for_cls] = cls
        return cls
    return decorate


# -----BEGIN COMMON FUNCTIONS-----
apply = lambda f, *a: f(*a)


class UIMetaBare:
    pass


class UIMetaBase(GameViralContext):
    game: THBattle
    _me = None

    @property
    def me(self):
        if (me := self._me) is not None:
            return me
        else:
            g = self.game
            me = g.runner.core.game.theone_of(g)
            try:
                me = g.find_character(me)
            except (AttributeError, IndexError):
                pass
            self._me = me
            return me

    def my_turn(self):
        g = self.game
        me = self.me
        try:
            act = g.action_stack[-1]
        except IndexError:
            return False

        from thb import actions
        if not isinstance(act, actions.ActionStage):
            return False

        if act.target is not me: return False

        if not act.in_user_input: return False

        return True

    def limit1_skill_used(self, tag):
        me = self.me
        t = me.tags
        return t[tag] >= t['turn_count']

    def clickable(self):
        return False

    def is_action_valid(self, c, tl):
        return (False, 'BUG!')

    def build_handcard(self, cardcls, p=None):
        me = self.me
        from thb.cards.base import CardList
        cl = CardList(p or me, 'cards')
        c = cardcls()
        c.move_to(cl)
        return c

    def accept_cards(self, cl: Sequence[Card]):
        g = self.game
        try:
            act = g.hybrid_stack[-1]
            if act.cond(cl):  # type: ignore
                return True

        except (IndexError, AttributeError):
            pass

        return False


class N:

    @staticmethod
    def card(c, conj='、'):
        if isinstance(c, (list, tuple)):
            return conj.join([N.card(i) for i in c])

        from thb.cards.base import Card, HiddenCard

        if isinstance(c, type):
            return f'<style=Card.Name>{c.ui_meta.name}</style>'

        if c.is_card(HiddenCard):
            return '一张牌'

        num = ' A23456789_JQK'[c.number]
        if num == '_': num = '10'

        if c.suit == Card.SPADE:
            suitnum = f'<style=Card.Black>♠{num}</style>'
        elif c.suit == Card.HEART:
            suitnum = f'<style=Card.Red>♥{num}</style>'
        elif c.suit == Card.CLUB:
            suitnum = f'<style=Card.Black>♣{num}</style>'
        elif c.suit == Card.DIAMOND:
            suitnum = f'<style=Card.Red>♦{num}</style>'
        elif c.suit == Card.NOTSET:
            suitnum = ''
        else:
            suitnum = '错误'

        return f'{suitnum}<style=Card.Name>{c.ui_meta.name}</style>'

    @staticmethod
    def char(ch, conj='、'):
        if isinstance(ch, (list, tuple)):
            return conj.join([N.char(i) for i in ch])
        m = ch.ui_meta
        return f'<style=Char.Name>{m.name}</style>'
