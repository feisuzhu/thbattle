# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.minoriko)


class Foison:
    # Skill
    name = u'丰收'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FoisonDrawCardStage:
    def effect_string(act):
        return u'大丰收！|G【%s】|r一下子收获了%d张牌！' % (
            act.source.ui_meta.char_name,
            act.amount,
        )


class AutumnFeast:
    # Skill
    name = u'秋祭'

    def clickable(game):
        me = game.me
        if not my_turn(): return False
        if limit1_skill_used('autumnfeast_tag'): return False

        if not (me.cards or me.showncards or me.equips):
            return False

        return True

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        from gamepack.thb.cards import Card
        if len(cl) != 2 or any(c.color != Card.RED for c in cl):
            return (False, u'请选择2张红色的牌！')
        return (True, u'发麻薯啦~')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        return (
            u'|G【%s】|r：麻薯年年有，今年特别多！'
        ) % (
            source.ui_meta.char_name,
        )


class AkiTribute:
    # Skill
    name = u'上贡'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Minoriko:
    # Character
    char_name = u'秋穰子'
    port_image = gres.minoriko_port
    description = (
        u'|DB没人气的丰收神 秋穰子 体力：3|r\n\n'
        u'|G丰收|r：|B锁定技|r，摸牌阶段摸牌后，若你的手牌数不足5张，你可以补至5张。\n\n'
        u'|G秋祭|r：你可以将两张红色的手牌或装备牌当作【五谷丰登】使用。一回合限一次。\n\n'
        u'|G上贡|r：|B锁定技|r，任何人使用【五谷丰登】时，你首先拿牌。在【五谷丰登】结算完毕后，若仍有牌没有被拿走，你将这些牌收入明牌区。\n\n'
        u'|DB（画师：Pixiv ID 5931998）|r'
    )
