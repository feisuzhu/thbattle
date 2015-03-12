# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions, cards
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import G, gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(cards)


class MassiveDamageCard:
    # action_stage meta
    image = 'thb-card-question'
    name = u'99 Damage'
    description = name

    def is_action_valid(g, cl, target_list):
        return (True, u'Massive Damage')
