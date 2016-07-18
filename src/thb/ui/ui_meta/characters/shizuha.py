# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid
from utils import BatchList


# -- code --
__metaclass__ = gen_metafunc(characters.shizuha)


class AutumnWindEffect:
    def effect_string(act):
        return u'|G秋风|r带走了|G【%s】|r的%s。' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )


class AutumnWindAction:

    def effect_string_before(act):
        tl = BatchList(act.target_list)
        return u'当|G秋风|r吹起，|G【%s】|r连牌都拿不住的时候，才回想起，妈妈说的对，要穿秋裤。' % (
            u'】|r、|G【'.join(tl.ui_meta.name),
        )

    def sound_effect(act):
        return 'thb-cv-shizuha_autumnwind'


class Decay:
    # Skill
    name = u'凋零'
    description = u'|B锁定技|r。你的回合内，一名其他角色失去最后一张手牌时，你摸一张牌。你的回合外，你受到一次伤害后，当前角色弃牌阶段需要额外弃置一张手牌。|r'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DecayAction:

    def effect_string(act):
        return u'|G【%s】|r觉得屁股凉了一下……' % act.target.ui_meta.name


class DecayEffect:

    def effect_string(act):
        return u'|G【%s】|r的|G凋零|r效果生效了。' % act.target.ui_meta.name

    def sound_effect(act):
        return 'thb-cv-shizuha_decay'


class DecayDrawCards:

    def sound_effect(act):
        return 'thb-cv-shizuha_decay'


class AutumnWind:
    # Skill
    name = u'秋风'
    description = u'你的弃牌阶段结束时，你可以弃置至多X名其他角色各一张牌（X为你弃牌阶段的弃牌数）。|r'

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
    name        = u'秋静叶'
    title       = u'寂寞与终焉的象征'
    illustrator = u'和茶'
    cv          = u'VV'
    designer    = u'SmiteOfKing'

    port_image        = u'thb-portrait-shizuha'
    figure_image      = u'thb-figure-shizuha'
    miss_sound_effect = u'thb-cv-shizuha_miss'
