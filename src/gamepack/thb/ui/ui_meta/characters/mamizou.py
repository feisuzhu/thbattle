# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, meta_property, my_turn
from utils import BatchList

# -- code --
__metaclass__ = gen_metafunc(characters.mamizou)


class Morphing:
    # Skill
    name = u'变化'

    @meta_property
    def params_ui(self):
        from gamepack.thb.ui.inputs import UIMorphingCardSelection
        return UIMorphingCardSelection

    def clickable(game):
        me = game.me

        if limit1_skill_used('mamizou_morphing_tag'):
            return False

        if not (my_turn() and (me.cards or me.showncards)):
            return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.mamizou.Morphing)
        cl = skill.associated_cards
        if len(cl) != 2 or any([c.resides_in.type not in ('cards', 'showncards') for c in cl]):
            return (False, u'请选择两张手牌！')

        cls = skill.get_morph_cls()
        if not cls:
            return (False, u'请选择需要变化的牌')

        if not skill.is_morph_valid():
            return (False, u'选择的变化牌不符和规则')

        return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        tl = BatchList(act.target_list)
        cl = BatchList(card.associated_cards)
        s = u'|G【%s】|r发动了|G变化|r技能，将|G%s|r当作|G%s|r对|G【%s】|r使用。' % (
            source.ui_meta.char_name,
            u'|r、|G'.join(cl.ui_meta.name),
            card.treat_as.ui_meta.name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
        )

        return s

    def sound_effect(act):
        return 'thb-cv-mamizou_morph'


class Mamizou:
    # Character
    char_name = u'二岩猯藏'
    port_image = 'thb-portrait-mamizou'
    miss_sound_effect = 'thb-cv-mamizou_miss'
    description = (
        u'|DB大狸子 二岩猯藏 体力：4|r\n\n'
        u'|G变化|r：出牌阶段限一次，你将两张手牌当做任何一张基本牌或非延时符卡使用。按此法使用的两张牌中至少有一张必须和你声明的牌类别一致。\n\n'
        u'|RKOF不平衡角色\n\n'
        u'|DB（人物设计：鵺子丶爱丽丝， 画师：Pixiv ID 36199915，CV：shourei小N）|r'
    )
