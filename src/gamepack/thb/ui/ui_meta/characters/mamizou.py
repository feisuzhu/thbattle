# -*- coding: utf-8 -*-

from gamepack.thb import cards, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn
from gamepack.thb.ui.resource import resource as gres
from client.ui.controls import Panel, Colors, Button
from utils import BatchList


__metaclass__ = gen_metafunc(characters.mamizou)


class MorphingCardSelectionUI(Panel):
    def __init__(self, parent, *a, **k):
        w, h = 480, 300  # 15 + (70+5)*6 + 15, 15 + (25+2) * 10 + 15
        x = (parent.width - w) // 2
        y = (parent.height - h) // 2
        Panel.__init__(self, x=x, y=y, width=w, height=h, parent=parent, zindex=10, *a, **k)
        self.view = view = parent
        view.add_observer('selection_change', self.on_selection_change)
        self.buttons = {}
        self.on_selection_change()

    def on_selection_change(self):
        view = self.view
        params = view.get_action_params()
        selection = cards.Card.card_classes.get(params.get('mamizou_morphing'))

        self.buttons = buttons = {}
        [b.delete() for b in self.control_list[:]]

        cl = view.get_selected_cards()
        if len(cl) != 2:
            return

        cats = set(cl[0].category)
        cats.update(cl[1].category)

        if 'skill' in cats:
            return

        cats = cats & {'basic', 'spellcard'}
        if not cats:
            return

        if 'spellcard' in cats:
            cats.discard('spellcard')
            cats.add('instant_spellcard')

        classes = [
            cls for cls in cards.Card.card_classes.values()
            if set(cls.category) & cats
        ]

        for i, cls in enumerate(classes):
            y, x = divmod(i, 6)
            b = Button(
                cls.ui_meta.name,
                parent=self, color=self.category_color(cls.category),
                x=15 + 75 * x, y=300 - 15 - (y+1)*27, width=70, height=25,
            )

            b.cls = cls
            buttons[cls] = b

            if selection is cls:
                b.color = Colors.orange

            @b.event
            def on_click(b=b):
                selection = cards.Card.card_classes.get(params.get('mamizou_morphing'))
                if b.cls is selection:
                    return

                clsname = b.cls.__name__
                last = self.buttons.get(selection)
                if last:
                    last.color = self.category_color(last.cls.category)

                b.color = Colors.orange
                params['mamizou_morphing'] = clsname
                self.view.notify('selection_change')

    def delete(self):
        self.view.remove_observer('selection_change', self.on_selection_change)
        Panel.delete(self)

    def category_color(self, category):
        return Colors.blue if 'basic' in category else Colors.green


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


class Mamizou:
    # Character
    char_name = u'二岩猯藏'
    port_image = gres.mamizou_port
    description = (
        u'|DB大狸子 二岩猯藏 体力：4|r\n\n'
        u'|G变化|r：出牌阶段限一次，你将两张手牌当做任何一张基本牌或非延时符卡使用。按此法使用的两张牌中至少有一张必须和你声明的牌类别一致。\n\n'
        u'|R8人身份场专属\n\n|r'
        u'|DB（人物设计：鵺子丶爱丽丝）|r'
    )
