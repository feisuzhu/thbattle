# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid
from utils import BatchList


# -- code --
__metaclass__ = gen_metafunc(characters.shizuha)


class AutumnWindEffect:
    def effect_string(act):
        return u'|G秋风|r带走了|G【%s】|r的%s。' % (
            act.target.ui_meta.char_name,
            card_desc(act.card),
        )


class AutumnWindAction:

    def effect_string_before(act):
        tl = BatchList(act.target_list)
        return u'当|G秋风|r吹起，|G【%s】|r连牌都拿不住的时候，才回想起，妈妈说的对，要穿秋裤。' % (
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

    def sound_effect(act):
        return 'thb-cv-shizuha_autumnwind'


class Decay:
    # Skill
    name = u'凋零'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DecayAction:

    def effect_string(act):
        return u'|G【%s】|r觉得屁股凉了一下……' % act.target.ui_meta.char_name


class DecayEffect:

    def effect_string(act):
        return u'|G【%s】|r的|G凋零|r效果生效了。' % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-shizuha_decay'


class DecayDrawCards:

    def sound_effect(act):
        return 'thb-cv-shizuha_decay'


class AutumnWind:
    # Skill
    name = u'秋风'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AutumnWindHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【秋风】吗？'

    def target(pl):
        if not pl:
            return (False, u'秋风：请选择目标玩家')

        return (True, u'秋风弃牌')


class Shizuha:
    # Character
    char_name = u'秋静叶'
    port_image = 'thb-portrait-shizuha'
    miss_sound_effect = 'thb-cv-shizuha_miss'
    description = (
        u'|DB寂寞与终焉的象征 秋静叶 体力：3|r\n\n'
        u'|G凋零|r：|B锁定技|r。你的回合内，一名其他角色失去最后一张手牌时，你摸一张牌。你的回合外，你受到一次伤害后，当前角色弃牌阶段需要额外弃置一张手牌。|r\n\n'
        # 叶子的离去，是因为风的追求，还是树的不挽留？
        u'|G秋风|r：你的弃牌阶段结束时，你可以弃置至多X名其他角色各一张牌（X为你弃牌阶段的弃牌数）。|r\n\n'
        # 觉得冷吗，谁叫你们不穿秋裤！（幸灾乐祸地）
        u'|DB（画师：Pixiv ID 42826425，CV：VV，人物设计：SmiteOfKing）|r'
        # 咦，黑幕来了，大家快逃！
    )
