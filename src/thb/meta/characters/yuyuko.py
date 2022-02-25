# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.yuyuko.Yuyuko)
class Yuyuko:
    # Character
    name        = '西行寺幽幽子'
    title       = '幽冥阁楼的吃货少女'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-yuyuko'
    figure_image      = 'thb-figure-yuyuko'
    miss_sound_effect = 'thb-cv-yuyuko_miss'

    notes = 'KOF不平衡角色'


@ui_meta(characters.yuyuko.GuidedDeath)
class GuidedDeath:
    # Skill
    name = '诱死'
    description = '出牌阶段限一次，你可以令一名其它角色失去一点体力，然后其于回合结束阶段回复一点体力。回合结束阶段，若你于出牌阶段没有发动过该技能，则所有体力值为1的其它角色失去一点体力。'

    def clickable(self):
        me = self.me
        if ttags(me)['guided_death_active_use']:
            return False

        if not self.my_turn():
            return False

        return True

    def is_action_valid(self, sk, tl):
        assert sk.is_card(characters.yuyuko.GuidedDeath)
        cards = sk.associated_cards

        if len(cards) != 0:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '请选择<style=Skill.Name>诱死</style>发动的目标')

        return (True, '发动<style=Skill.Name>诱死</style>（回合结束时不再发动第二效果）')

    def effect_string(self, act):
        return f'{N.char(act.source)}将{N.char(act.target)}献祭给了西行妖。'

    def sound_effect(self, act):
        return 'thb-cv-yuyuko_pcb'


@ui_meta(characters.yuyuko.SoulDrain)
class SoulDrain:
    # Skill
    name = '离魂'
    description = (
        '你的回合内，当一名其它角色进入濒死状态时，你摸一张牌，然后你可以与该角色拼点：'
        '<style=Desc.Li>若你赢，则将其体力上限改为1。</style>'
        '<style=Desc.Li>若你没赢，则将其体力值改为1。</style>'
    )


@ui_meta(characters.yuyuko.PerfectCherryBlossom)
class PerfectCherryBlossom:
    # Skill
    name = '反魂'
    description = (
        '<style=B>锁定技</style>，一名角色被击坠后，你可以增加一点体力上限或回复一点体力。你的手牌上限是你的体力上限。'
    )


@ui_meta(characters.yuyuko.PerfectCherryBlossomExtractAction)
class PerfectCherryBlossomExtractAction:
    choose_option_prompt = '<style=Skill.Name>返魂</style>：请选择你要的效果'
    choose_option_buttons = (('回复体力', 'life'), ('增加体力上限', 'maxlife'))

    def effect_string_before(self, act):
        return '幽雅地绽放吧，墨染的樱花！西行妖的力量又增强了一些。'

    def sound_effect_before(self, act):
        return 'thb-cv-yuyuko_pcb_extract'


@ui_meta(characters.yuyuko.GuidedDeathEffect)
class GuidedDeathEffect:
    def effect_string_apply(self, act):
        return f'{N.char(act.source)}：“既然在座的各位中暑的中暑，受伤的受伤，不如都到花下沉眠吧！”'


@ui_meta(characters.yuyuko.SoulDrainEffect)
class SoulDrainEffect:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>离魂</style>吗？'

    def effect_string_apply(self, act):
        return f'{N.char(act.source)}微笑着站在一旁。{N.char(act.target)}似乎离死亡更近了一点。'

    def sound_effect_before(self, act):
        return random.choice([
            'thb-cv-yuyuko_souldrain1',
            'thb-cv-yuyuko_souldrain2',
        ])
