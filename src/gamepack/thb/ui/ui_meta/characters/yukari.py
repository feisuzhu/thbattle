# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres
from utils import BatchList

__metaclass__ = gen_metafunc(characters.yukari)


class Realm:
    # Skill
    name = u'境界'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RealmSkipFatetell:
    def effect_string_before(act):
        return u'|G【%s】|r 发动了|G境界|r，跳过了判定阶段。' % (
            act.target.ui_meta.char_name,
        )


class RealmSkipFatetellHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过判定阶段')
        else:
            return (False, u'请弃置一张手牌，跳过判定阶段')


class RealmSkipDrawCard:
    def effect_string_before(act):
        tl = BatchList(act.pl)
        return u'|G【%s】|r发动了|G境界|r，跳过了摸牌阶段，并抽取了|G【%s】|r的手牌。' % (
            act.target.ui_meta.char_name,
            u'】|r和|G【'.join(tl.ui_meta.char_name),
        )


class RealmSkipDrawCardHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过摸牌阶段，并获得任意1～2名角色的一张手牌')
        else:
            return (False, u'请弃置一张手牌，跳过摸牌阶段')

    # choose_players
    def target(tl):
        if not tl:
            return (False, u'请选择1-2名其他玩家，随机出抽取一张手牌')

        return (True, u'跳过摸牌阶段，并获得任意1～2名角色的一张手牌')


class RealmSkipAction:
    # choose_option meta
    choose_option_buttons = ((u'相应区域', True), (u'手牌区', False))
    choose_option_prompt = u'你要将这张卡牌移动到何处？'

    def effect_string_before(act):
        return u'|G【%s】|r发动了|G境界|r，跳过了出牌阶段，并移动了场上的卡牌。' % (
            act.target.ui_meta.char_name,
        )


class RealmSkipActionHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'跳过出牌阶段，并移动场上卡牌')
        else:
            return (False, u'请弃置一张手牌，跳过出牌阶段')

    # choose_players
    def target(tl):
        if not tl:
            return (False, u'[出牌]将第一名玩家的装备/判定牌移至第二名玩家的相应区域')

        rst = bool(tl[0].equips or tl[0].fatetell)
        if rst:
            return (len(tl) == 2, u'[出牌]将第一名玩家的装备/判定牌移至第二名玩家的相应区域')
        else:
            return (False, u'第一名玩家没有牌可以让你移动！')


class RealmSkipDropCard:
    def effect_string_before(act):
        return u'|G【%s】|r发动了|G境界|r，跳过了弃牌阶段。' % (
            act.target.ui_meta.char_name,
        )


class RealmSkipDropCardHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置一张牌，跳过弃牌阶段')
        else:
            return (False, u'弃置一张手牌，跳过弃牌阶段')


class Yukari:
    # Character
    char_name = u'八云紫'
    port_image = gres.yukari_port
    figure_image = gres.yukari_figure
    description = (
        u'|DB永远17岁 八云紫 体力：4|r\n\n'
        u'|G境界|r：你可以弃置一张手牌并跳过你的一个阶段（准备阶段和结束阶段除外）\n'
        u'|B|R>>|r 若你跳过摸牌阶段，你可以获得至多2名其他角色的各一张手牌；\n'
        u'|B|R>>|r 若你跳过出牌阶段，你可以将场上的一张牌移动到另一名角色区域里的相应位置（不可替换原装备），或将其交给一名角色。\n\n'
        u'|DB（画师：渚FUN）|r'
    )
