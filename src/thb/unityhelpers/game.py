# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions
# -- code --
'''

def get_identity_def(g):
    # [('hakurei', u'博丽'), ...]
    tbl = sorted(g.ui_meta.identity_table.items())
    return [(g.ui_meta.IdentityType.rlookup(i[0]).lower(), i[1]) for i in tbl]


def get_revealed_identity_def(g, act, p, ch):
    if not isinstance(act, actions.RevealRole):
        return

    if act.target not in (p, ch):
        return

    me = g.me
    if not act.can_be_seen_by(me):
        return

    return lookup_identity(g, act.target)


def lookup_identity(g, p):
    try:
        t = p.identity.type
        return (g.ui_meta.IdentityType.rlookup(t).lower(), g.ui_meta.identity_table[t])
    except AttributeError:
        return None


def modename2display(modename: str) -> str:
    from thb import modes
    gcls = modes.get(modename)
    if not gcls:
        return '未知模式'
    else:
        return gcls.ui_meta.name

'''
