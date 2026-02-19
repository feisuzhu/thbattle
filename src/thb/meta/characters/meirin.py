# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.cards.classes import AttackCard, GrazeCard
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.meirin.RiverBehind)
class RiverBehind:
    # Skill
    name = '背水'
    description = (
        '<style=B>觉醒技</style>，准备阶段开始时，若你体力为全场最低或之一且不大于2时，你减1点体力上限并获得技能<style=Skill.Name>太极</style>。'
        '<style=Desc.Li><style=Skill.Name>太极</style>：你可将<style=Card.Name>弹幕</style>当<style=Card.Name>擦弹</style>，<style=Card.Name>擦弹</style>当<style=Card.Name>弹幕</style>使用或打出。</style>'
    )


@ui_meta(characters.meirin.Taichi)
class Taichi:
    # Skill
    name = '太极'
    description = '你可将<style=Card.Name>弹幕</style>当<style=Card.Name>擦弹</style>，<style=Card.Name>擦弹</style>当<style=Card.Name>弹幕</style>使用或打出。'

    def clickable(self):
        g = self.game

        act = g.action_stack[-1]
        if isinstance(act, actions.ActionStage):
            return True

        if self.accept_cards([self.build_handcard(AttackCard)]):
            return True

        if self.accept_cards([self.build_handcard(GrazeCard)]):
            return True

        return False

    def is_complete(self, skill):
        cl = skill.associated_cards
        from thb.cards.classes import AttackCard, GrazeCard
        if len(cl) != 1 or not (cl[0].is_card(AttackCard) or cl[0].is_card(GrazeCard)):
            return (False, '请选择一张<style=Card.Name>弹幕</style>或者<style=Card.Name>擦弹</style>！')
        return (True, '动之则分，静之则合。无过不及，随曲就伸')

    def is_action_valid(self, sk, tl):
        rst, reason = self.is_complete(sk)
        if not rst:
            return (rst, reason)
        else:
            return sk.treat_as().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        return f'动之则分，静之则合。无过不及，随曲就伸……{N.char(src)}凭<style=Skill.Name>太极</style>之势，轻松应对。'

    def sound_effect(self, act):
        return 'thb-cv-meirin_taichi'


@ui_meta(characters.meirin.LoongPunch)
class LoongPunch:
    # Skill
    name = '龙拳'
    description = '每当你使用的<style=Card.Name>弹幕</style>被其他角色使用的<style=Card.Name>擦弹</style>抵消时，或其他角色使用的<style=Card.Name>弹幕</style>被你使用的<style=Card.Name>擦弹</style>抵消时，你可以弃置其1张手牌。'


@ui_meta(characters.meirin.LoongPunchHandler)
class LoongPunchHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>龙拳</style>吗？'


@ui_meta(characters.meirin.LoongPunchAction)
class LoongPunchAction:
    def effect_string_before(self, act):
        src, tgt = act.source, act.target
        if act.type == 'attack':
            return f'{N.char(tgt)}闪过了<style=Card.Name>弹幕</style>，却没有闪过{N.char(src)}的拳劲，一张手牌被{N.char(src)}震飞！'
        if act.type == 'graze':
            return f'{N.char(src)}擦过弹幕，随即以拳劲沿着弹幕轨迹回震，{N.char(tgt)}措手不及，一张手牌掉在了地上。'

    def sound_effect(self, act):
        return 'thb-cv-meirin_loongpunch'


@ui_meta(characters.meirin.RiverBehindAwake)
class RiverBehindAwake:
    def effect_string_before(self, act):
        return f'{N.char(act.target)}发现自己处境危险，竟参悟了<style=Skill.Name>太极</style>拳！'

    def sound_effect(self, act):
        return 'thb-cv-meirin_rb'


@ui_meta(characters.meirin.Meirin)
class Meirin:
    # Character
    name        = '红美铃'
    title       = '我只打盹我不翘班'
    illustrator = '霏茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-meirin'
    figure_image      = 'thb-figure-meirin'
    miss_sound_effect = ('thb-cv-meirin_miss1', 'thb-cv-meirin_miss2')
