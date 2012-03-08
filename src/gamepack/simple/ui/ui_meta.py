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

class UseGraze:
    # choose_card meta
    image = gres.card_graze
    text_valid = u'我闪！'
    text = u'请出闪...'

class DropCardStage:
    # choose_card meta
    text_valid = u'OK，就这些了'
    text = u'请弃牌...'

class RejectHandler:
    # choose_card meta
    text_valid = u'对不起，你是一个好人...'
    text = u'请选择一张好人卡'

# -----END ACTIONS UI META-----

# -----BEGIN CARDS UI META-----
__metaclass__ = gen_metafunc(cards)

class HiddenCard:
    image = cres.card_hidden
    name = u'这个是隐藏卡片，你不应该看到它'

    def is_action_valid(cards, source, target_list):
        return (False, u'这是BUG，你没法发动这张牌...')

class AttackCard:
    # action_stage meta
    image = gres.card_attack
    name = u'杀'

    def is_action_valid(cards, source, target_list):
        if not target_list:
            return (False, u'请选择杀的目标')
        target = target_list[0]
        if target.dead:
            return (False, u'禁止鞭尸！')

        if source == target:
            return (True, u'您真的要自残么？！')
        else:
            return (True, u'来一发！')

class GrazeCard:
    name = u'闪'
    image = gres.card_graze
    def is_action_valid(cards, source, target_list):
        return (False, u'你不能主动出闪')

class HealCard:
    # action_stage meta
    image = gres.card_heal
    name = u'药'

    def is_action_valid(cards, source, target_list):
        target = target_list[0]
        if not source == target:
            return (False, u'BUG!!!!')

        if target.life >= target.maxlife:
            return (False, u'您的体力值已达到上限')
        else:
            return (True, u'嗑一口，精神焕发！')

class DemolitionCard:
    # action_stage meta
    image = gres.card_demolition
    name = u'釜底抽薪'

    def is_action_valid(cards, source, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target= target_list[0]
        if source == target:
            return (True, u'还是拆别人的吧...')
        elif not len(target.cards):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

class RejectCard:
    name = u'好人卡'
    image = gres.card_reject

    def is_action_valid(cards, source, target_list):
        return (False, u'你不能主动出好人卡')

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
        if me.stage == game.ACTION_STAGE and me.cards:
            return True
        return False

    def is_action_valid(skill, source, target_list):
        skill = skill[0]
        assert isinstance(skill, characters.Envy)
        if len(skill.associated_cards) != 1:
            return (False, u'请选择一张牌！')
        else:
            return cards.DemolitionCard.ui_meta.is_action_valid([skill], source, target_list)

# ----------

class Youmu:
    # Character
    char_name = u'魂魄妖梦'
    port_image = gres.youmu_port

class Nitoryu:
    # Skill
    name = u'二刀流'

    def clickable(game):
        return False

    def is_action_valid(skill, source, target_list):
        return (False, 'BUG!')

# ----------

# -----END CHARACTERS UI META-----
