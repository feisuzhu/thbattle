# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions
# -- code --


def get_identity_def(g):
    # [('hakurei', u'博丽'), ...]
    tbl = sorted(g.ui_meta.identity_table.items())
    return [(g.ui_meta.IdentityType.rlookup(i[0]).lower(), i[1]) for i in tbl]


def get_revealed_identity_def(g, act, p, ch):
    if not isinstance(act, actions.RevealIdentity):
        return

    if act.target not in (p, ch):
        return

    me = g.me
    if not act.can_see(me):
        return

    t = act.target.identity.type
    return (g.ui_meta.IdentityType.rlookup(t).lower(), g.ui_meta.identity_table[t])
