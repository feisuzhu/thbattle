# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.resource import resource as gres
from utils import BatchList

__metaclass__ = gen_metafunc(characters.sp_yukari)


class SpiritingAway:
    # Skill
    name = u'神隐'

    def clickable(game):
        me = game.me
        if me.tags['spirit_away_tag'] >= 2: return False
        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'请选择一名玩家')

        tgt = tl[0]
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        if not any(getattr(tgt, i) for i in catnames):
            return (False, u'这货已经没有牌了')

        return (True, u'发动【神隐】')


class SpYukari:
    # Character
    char_name = u'SP八云紫'
    port_image = gres.sp_yukari_port
    figure_image = gres.sp_yukari_figure
    description = (
        u'|DB神隐的主犯 八云紫 体力：4|r\n\n'
        u'|G神隐|r：出牌阶段限两次，你可以将任意角色区域内的一张牌移出游戏。你的回合结束阶段，那名玩家获得那张牌。\n\n'
        u'|DB（画师：Vivicat from 幻想梦斗符）|r'
    )
