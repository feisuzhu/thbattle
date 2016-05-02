# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import thbdebug
from thb.ui.ui_meta.common import gen_metafunc, meta_property


# -- code --
__metaclass__ = gen_metafunc(thbdebug)


class DebugUseCard:
    # Skill
    name = u'转化'
    params_ui = 'UIDebugUseCardSelection'

    @meta_property
    def image(c):
        return c.treat_as.ui_meta.image

    @meta_property
    def image_small(c):
        return c.treat_as.ui_meta.image_small

    @meta_property
    def tag_anim(c):
        return c.treat_as.ui_meta.tag_anim

    description = u'DEBUG'

    def clickable(game):
        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        try:
            skill.treat_as.ui_meta
        except:
            return False, u'Dummy'

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def is_complete(g, cl):
        return True, u'XXX'


class DebugDecMaxLife:
    # Skill
    name = u'减上限'

    def clickable(g):
        return True

    def is_action_valid(g, cl, target_list):
        acards = cl[0].associated_cards
        if len(acards):
            return (False, u'请不要选择牌！')

        return (True, u'XXX')
