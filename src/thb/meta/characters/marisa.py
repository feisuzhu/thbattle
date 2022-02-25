# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.marisa.Marisa)
class Marisa:
    # Character
    name        = '雾雨魔理沙'
    title       = '绝非普通的强盗少女'
    illustrator = '霏茶'
    cv          = '君寻'

    port_image        = 'thb-portrait-marisa'
    figure_image      = 'thb-figure-marisa'
    miss_sound_effect = 'thb-cv-marisa_miss'


@ui_meta(characters.marisa.Daze)
class Daze:
    name = '打贼'

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}喊道：“打贼啦！”向{N.char(act.target)}使用了<style=Card.Name>弹幕</style>。'


@ui_meta(characters.marisa.BorrowAction)
class BorrowAction:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要视为对魔理沙使用弹幕吗？'


@ui_meta(characters.marisa.Borrow)
class Borrow:
    # Skill
    name = '借走'
    description = '出牌阶段限一次，你可以获得其他角色的一张牌，然后该角色可以视为对你使用了一张<style=Card.Name>弹幕</style>。'

    def clickable(self):
        if self.limit1_skill_used('borrow_tag'):
            return False

        if not self.my_turn(): return False

        return True

    def is_action_valid(self, sk, tl):
        if sk.associated_cards:
            return (False, '请不要选择牌!')

        if len(tl) != 1:
            return (False, '请选择1名玩家')

        tgt = tl[0]
        if not (tgt.cards or tgt.showncards or tgt.equips):
            return (False, '目标没有牌可以“借给”你')

        return (True, '我死了以后你们再拿回去好了！')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'大盗{N.char(act.source)}“<style=Skill.Name>借走</style>”了{N.char(act.target)}的牌。'

    def sound_effect(self, act):
        return 'thb-cv-marisa_borrow'
