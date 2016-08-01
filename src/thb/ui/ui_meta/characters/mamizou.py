# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from utils import BatchList

# -- code --
__metaclass__ = gen_metafunc(characters.mamizou)


class Morphing:
    # Skill
    name = u'变化'
    description = u'出牌阶段限一次，你可以将两张手牌当任意基本牌或非延时符卡使用，这两张牌中至少有一张须与你声明使用的牌类型相同。'

    params_ui = 'UIMorphingCardSelection'

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
            source.ui_meta.name,
            u'|r、|G'.join(cl.ui_meta.name),
            card.treat_as.ui_meta.name,
            u'】|r、|G【'.join(tl.ui_meta.name),
        )

        return s

    def sound_effect(act):
        return 'thb-cv-mamizou_morph'


class Mamizou:
    # Character
    name        = u'二岩猯藏'
    title       = u'大狸子'
    designer    = u'鵺子丶爱丽丝'
    illustrator = u'hacko.@星の妄想乡'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-mamizou'
    figure_image      = u'thb-figure-mamizou'
    miss_sound_effect = u'thb-cv-mamizou_miss'

    notes = u'|RKOF模式不可用'
