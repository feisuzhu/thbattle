# -*- coding: utf-8 -*-

from gamepack.thb import cards, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from gamepack.thb.ui.resource import resource as gres
from gamepack.thb.ui.game_controls import CardSelectionPanel
from utils import BatchList


__metaclass__ = gen_metafunc(characters.mamizou)


card_categories = {
    cat: [
        cls() for cls in cards.Card.card_classes.values()
        if cat in cls.category
    ] for cat in ('basic', 'instant_spellcard')
}

cat_names = (
    ('basic', u'基本牌'),
    ('instant_spellcard', u'符卡')
)


class MorphingCardSelectionUI(CardSelectionPanel):
    def __init__(self, parent, *a, **k):
        CardSelectionPanel.__init__(self, parent=parent, zindex=10, *a, **k)
        self.view = view = parent
        view.selection_change += self.on_selection_change
        self.panel = None
        self.on_selection_change()

    def on_selection_change(self):
        view = self.view
        params = view.get_action_params()
        cl = view.get_selected_cards()

        def cancel():
            if self.panel:
                self.panel.delete()
                self.panel = None
                try:
                    del params['mamizou_morphing']
                except:
                    pass

        if len(cl) != 2:
            return cancel()

        cats = set(cl[0].category)
        cats.update(cl[1].category)

        if 'skill' in cats:
            return cancel()

        cats = cats & {'basic', 'spellcard'}
        if not cats:
            return cancel()

        if self.panel:
            return

        if 'spellcard' in cats:
            cats.discard('spellcard')
            cats.add('instant_spellcard')

        card_lists = [
            (name, card_categories[cat])
            for cat, name in cat_names
            if cat in cats
        ]
        self.panel = panel = CardSelectionPanel(
            parent=self.parent, zindex=10,
            selection_mode=CardSelectionPanel.SINGLE,
        )
        panel.init(card_lists, multiline=len(card_lists) < 2)

        @panel.event
        def on_selection_change():
            if panel.selection:
                card = panel.selection[0].associated_card
                params['mamizou_morphing'] = card.__class__.__name__
            else:
                try:
                    del params['mamizou_morphing']
                except:
                    pass

            self.view.selection_change.notify()

    def delete(self):
        if self.panel:
            self.panel.delete()

        self.view.selection_change -= self.on_selection_change
        super(MorphingCardSelectionUI, self).delete()


class Morphing:
    # Skill
    name = u'变化'
    params_ui = MorphingCardSelectionUI

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
        return gres.cv.mamizou_morph


class Mamizou:
    # Character
    char_name = u'二岩猯藏'
    port_image = gres.mamizou_port
    miss_sound_effect = gres.cv.mamizou_miss
    description = (
        u'|DB大狸子 二岩猯藏 体力：4|r\n\n'
        u'|G变化|r：出牌阶段限一次，你将两张手牌当做任何一张基本牌或非延时符卡使用。按此法使用的两张牌中至少有一张必须和你声明的牌类别一致。\n\n'
        u'|RKOF不平衡角色\n\n'
        u'|DB（人物设计：鵺子丶爱丽丝， 画师：Pixiv ID 36199915，CV：shourei小N）|r'
    )
