# -*- coding: utf-8 -*-

from game.autoenv import Game
G = Game.getgame

from types import FunctionType
from collections import OrderedDict

metadata = OrderedDict()


class UIMetaAccesser(object):
    def __init__(self, obj, cls):
        self.obj = obj
        self.cls = cls

    def __getattr__(self, name):
        cls = self.cls
        if hasattr(cls, '_is_mixedclass'):
            l = list(cls.__bases__)
        else:
            l = [cls]

        while l:
            c = l.pop(0)
            try:
                val = metadata[c][name]

                if isinstance(val, FunctionType) and getattr(val, '_is_property', False):
                    val = val(self.obj or self.cls)

                return val

            except KeyError:
                pass
            b = c.__base__
            if b is not object: l.append(b)
        raise AttributeError('%s.%s' % (self.cls.__name__, name))


class UIMetaDescriptor(object):
    def __get__(self, obj, cls):
        return UIMetaAccesser(obj, cls)


def gen_metafunc(_for):
    def metafunc(clsname, bases, _dict):
        meta_for = getattr(_for, clsname)
        meta_for.ui_meta = UIMetaDescriptor()
        if meta_for in metadata:
            raise Exception('%s ui_meta redefinition!' % meta_for)

        metadata[meta_for] = _dict

        return _dict

    return metafunc


def meta_property(f):
    f._is_property = True
    return f


# -----BEGIN COMMON FUNCTIONS-----


def my_turn():
    g = G()

    try:
        act = g.action_stack[-1]
    except IndexError:
        return False

    from gamepack.thb import actions
    if not isinstance(act, actions.ActionStage):
        return False

    if act.target is not g.me: return False

    if not act.in_user_input: return False

    return True


def limit1_skill_used(tag):
    t = G().me.tags
    return t[tag] >= t['turn_count']


def passive_clickable(game):
    return False


def passive_is_action_valid(g, cl, target_list):
    return (False, 'BUG!')


def card_desc(c):
    if isinstance(c, (list, tuple)):
        return u'、'.join([card_desc(i) for i in c])

    from gamepack.thb.cards import Card, HiddenCard
    if c.is_card(HiddenCard): return u'一张牌'

    if c.suit == Card.SPADE:
        suit = u'|r♠'
    elif c.suit == Card.HEART:
        suit = u'|r|cb03a11ff♥'
    elif c.suit == Card.CLUB:
        suit = u'|r♣'
    elif c.suit == Card.DIAMOND:
        suit = u'|r|cb03a11ff♦'
    else:
        suit = u'|r错误'

    num = ' A23456789_JQK'[c.number]
    if num == '_': num = '10'
    return suit + num + ' |G%s|r' % c.ui_meta.name


def build_handcard(cardcls, p=None):
    from gamepack.thb.cards import CardList
    cl = CardList(p or G().me, 'cards')
    c = cardcls()
    c.move_to(cl)
    return c
