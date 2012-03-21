# -*- coding: utf-8 -*-
from .. import actions
from .. import cards
from .. import characters

import game
import types
import resource as gres
from client.ui import resource as cres

from utils import DataHolder

def gen_metafunc(_for):
    def metafunc(clsname, bases, _dict):
        meta_for = _for.__dict__.get(clsname)
        data = DataHolder.parse(_dict)
        meta_for.ui_meta = data

    return metafunc

# -----BEGIN ACTIONS UI META-----
__metaclass__ = gen_metafunc(actions)

class DropCardStage:
    # choose_card meta
    text_valid = u'OK，就这些了'
    text = u'请弃牌…'


# -----END ACTIONS UI META-----

# -----BEGIN CARDS UI META-----
__metaclass__ = gen_metafunc(cards)

class HiddenCard:
    # action_stage meta
    image = cres.card_hidden
    name = u'这个是隐藏卡片，你不应该看到它'

    def is_action_valid(cards, source, target_list):
        return (False, u'这是BUG，你没法发动这张牌…')

class AttackCard:
    # action_stage meta
    image = gres.card_attack
    name = u'击'

    def is_action_valid(cards, source, target_list):
        if not target_list:
            return (False, u'请选择击的目标')
        target = target_list[0]
        if target.dead:
            return (False, u'禁止鞭尸！')

        if source == target:
            return (True, u'您真的要自残么？！')
        else:
            return (True, u'来一发！')

class GrazeCard:
    # action_stage meta
    name = u'擦弹'
    image = gres.card_graze
    def is_action_valid(cards, source, target_list):
        return (False, u'你不能主动使用擦弹')

class UseGraze:
    # choose_card meta
    image = gres.card_graze
    text_valid = u'我闪！'
    text = u'请使用擦弹…'

class HealCard:
    # action_stage meta
    image = gres.card_heal
    name = u'桃'

    def is_action_valid(cards, source, target_list):
        target = target_list[0]
        if not source == target:
            return (False, u'BUG!!!!')

        if target.life >= target.maxlife:
            return (False, u'您的体力值已达到上限')
        else:
            return (True, u'来一口，精神焕发！')

class DemolitionCard:
    # action_stage meta
    image = gres.card_demolition
    name = u'城管执法'

    def is_action_valid(cards, source, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target= target_list[0]
        if source == target:
            return (True, u'还是拆别人的吧…')
        elif not len(target.cards):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

class RejectCard:
    # action_stage meta
    name = u'好人卡'
    image = gres.card_reject

    def is_action_valid(cards, source, target_list):
        return (False, u'你不能主动出好人卡')

class RejectHandler:
    # choose_card meta
    text_valid = u'对不起，你是一个好人…'
    text = u'请选择一张好人卡'

class SealingArrayCard:
    # action_stage meta
    name = u'封魔阵'
    image = gres.card_sealarray
    tag_anim = gres.tag_sealarray

    def is_action_valid(cards, source, target_list):
        if len(target_list) != 1:
            return (False, u'请选择封魔阵的目标')
        t = target_list[0]
        if source == t:
            return (True, u'你不能跟自己过不去啊！')

        return (True, u'画个圈圈诅咒你！')

class NazrinRodCard:
    # action_stage meta
    name = u'探宝棒'
    image = gres.card_nazrinrod

    def is_action_valid(cards, source, target_list):
        t = target_list[0]
        assert t is source
        return (True, u'看看能找到什么好东西~')

def equip_iav(cards, source, target_list):
    t = target_list[0]
    assert t is source
    return (True, u'配上好装备，不再掉节操！')

class OpticalCloakCard:
    # action_stage meta
    name = u'光学迷彩'
    image = gres.card_opticalcloak
    image_small = gres.card_opticalcloak_small

    is_action_valid = equip_iav

class OpticalCloakSkill:
    # Skill
    name = u'光学迷彩'

    def clickable(game):
        return False

    def is_action_valid(skill, source, target_list):
        return (False, 'BUG!')

class GreenUFOCard:
    # action_stage meta
    name = u'绿色UFO'
    image = gres.card_greenufo
    image_small = gres.card_greenufo_small

    is_action_valid = equip_iav

class GreenUFOSkill:
    # Skill
    name = u'绿色UFO'
    no_display = True

    def clickable(game):
        return False

    def is_action_valid(skill, source, target_list):
        return (False, 'BUG!')

class RedUFOCard:
    # action_stage meta
    name = u'红色UFO'
    image = gres.card_redufo
    image_small = gres.card_redufo_small

    is_action_valid = equip_iav

class RedUFOSkill:
    # Skill
    name = u'红色UFO'
    no_display = True

    def clickable(game):
        return False

    def is_action_valid(skill, source, target_list):
        return (False, 'BUG!')


# -----END CARDS UI META-----

# -----BEGIN CHARACTERS UI META-----
__metaclass__ = gen_metafunc(characters)

class Parsee:
    # Character
    char_name = u'水桥帕露西'
    port_image = gres.parsee_port

class Envy:
    # Skill
    name = u'嫉妒'

    def clickable(game):
        me = game.me
        if me.stage == game.ACTION_STAGE and me.cards: # FIXME: lit on 'choose_card'
            return True
        return False

    def is_action_valid(skill, source, target_list):
        skill = skill[0]
        assert isinstance(skill, characters.Envy)
        if len(skill.associated_cards) != 1:
            return (False, u'请选择一张牌！')
        else:
            return cards.DemolitionCard.ui_meta.is_action_valid([skill], source, target_list)

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|r发动了嫉妒技能，将|c208020ff%s|r当作|c208020ff%s|r对|c208020ff【%s】|r使用。' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            target.ui_meta.char_name,
        )
        return s

# ----------

class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port

class Mijincihangzhan:
    # Skill
    name = u'迷津慈航斩'

    def clickable(game):
        return False

    def is_action_valid(skill, source, target_list):
        return (False, 'BUG!')

# ----------

class LittleDevil:
    # Character
    char_name = u'小恶魔'
    port_image = gres.ldevil_port

class Find:
    # Skill
    name = u'寻找'

    def clickable(game):
        me = game.me
        if me.stage == game.ACTION_STAGE and me.cards:
            return True
        return False

    def is_action_valid(skill, source, target_list):
        skill = skill[0]
        assert isinstance(skill, characters.Find)
        if not len(skill.associated_cards):
            return (False, u'请选择需要换掉的牌！')

        if not [source] == target_list:
            return (False, 'BUG!!')

        return (True, u'换掉这些牌')

    def effect_string(act):
        # for effects.launch_effect
        source = act.source
        card = act.card
        target = act.target_list[0]
        s = u'|c208020ff【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.char_name,
            len(card.associated_cards),
        )
        return s

# -----END CHARACTERS UI META-----
