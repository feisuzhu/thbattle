# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, Optional, Sequence, TYPE_CHECKING, Type, Union

# -- third party --
# -- own --
from game.base import GameViralContext
from thb.characters.base import Character

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

    def card_desc(self, c):
        if isinstance(c, (list, tuple)):
            return '、'.join([self.card_desc(i) for i in c])

        from thb.cards.base import Card, HiddenCard
        if c.is_card(HiddenCard): return '一张牌'

        if c.suit == Card.SPADE:
            suit = '|r♠'
        elif c.suit == Card.HEART:
            suit = '|r|cb03a11ff♥'
        elif c.suit == Card.CLUB:
            suit = '|r♣'
        elif c.suit == Card.DIAMOND:
            suit = '|r|cb03a11ff♦'
        elif c.suit == Card.NOTSET:
            suit = '|r '
        else:
            suit = '|r错误'

        num = ' A23456789_JQK'[c.number]
        if num == '_': num = '10'
        return suit + num + ' |G%s|r' % c.ui_meta.name

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

    def char_desc(self, ch: Union[Character, Type[Character]]):
        m = ch.ui_meta

        cls: Type[Character]
        obj: Optional[Character]

        if isinstance(ch, Character):
            cls, obj = ch.__class__, ch
        else:
            cls, obj = ch, None

        rst = []
        rst.append('|DB%s %s 体力：%s|r' % (m.title, m.name, cls.maxlife))
        skills = list(cls.skills)
        if hasattr(cls, 'boss_skills'):
            skills.extend(cls.boss_skills)

        if obj:
            skills.extend([
                c for c in obj.skills
                if 'character' in c.skill_category and c not in skills
            ])

        for s in skills:
            sm = s.ui_meta
            rst.append('|G%s|r：%s' % (sm.name, sm.description))

        notes = getattr(m, 'notes', '')
        if notes:
            rst.append(notes)

        tail = ['%s：%s' % i for i in [
            ('画师',     getattr(m, 'illustrator', None)),
            ('CV',       getattr(m, 'cv', None)),
            ('人物设计', getattr(m, 'designer', None)),
        ] if i[1]]

        if tail:
            rst.append('|DB（%s）|r' % '，'.join(tail))

        return '\n\n'.join(rst)
