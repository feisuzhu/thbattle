# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.cards import definition
from thb.meta.common import ui_meta

# -- code --


@ui_meta(definition.MassiveDamageCard)
class MassiveDamageCard:
    # action_stage meta
    image = 'thb-card-question'
    name = '99 Damage'
    description = name

    def is_action_valid(self, g, cl, target_list):
        return (True, 'Massive Damage')
