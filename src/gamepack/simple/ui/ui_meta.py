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
    text = u'请出闪…'

class DropCardStage:
    # choose_card meta
    text_valid = u'OK，就这些了'
    text = u'请弃牌…'

class RejectHandler:
    # choose_card meta
    text_valid = u'对不起，你是一个好人…'
    text = u'请选择一张好人卡'

class Attack:
    #choose_card meta
    text_valid = u'杀！'
    text = u'请选择一张杀'

    # action_stage meta
    def is_action_valid(source, cards, target_list):
        if not target_list:
            return (False, u'请选择杀的目标')
        target = target_list[0]
        if target.dead:
            return (False, u'禁止鞭尸！')

        if source == target:
            return (True, u'您真的要自残么？！')
        else:
            return (True, u'来一发！')

class Heal:
    # action_stage meta
    def is_action_valid(source, cards, target_list):
        target = target_list[0]
        if not source == target:
            return (False, u'BUG!!!!')

        if target.life >= target.maxlife:
            return (False, u'您的体力值已达到上限')
        else:
            return (True, u'嗑一口，精神焕发！')

class Demolition:
    # action_stage meta
    def is_action_valid(source, cards, target_list):
        if not target_list:
            return (False, u'请选择拆除目标')

        target= target_list[0]
        if source == target:
            return (True, u'还是拆别人的吧…')
        elif not len(target.cards):
            return (False, u'这货已经没有牌了')
        else:
            return (True, u'嗯，你的牌太多了')

# -----END ACTIONS UI META-----

# -----BEGIN CARDS UI META-----
__metaclass__ = gen_metafunc(cards)

class HiddenCard:
    image = cres.card_hidden
    name = u'这个是隐藏卡片，你不应该看到它'
    passive_card_prompt = u'这是BUG，你没法发动这张牌…'

class AttackCard:
    # action_stage meta
    target = 1
    image = gres.card_attack
    name = u'杀'
    #passive_card_prompt = u'xxx'

class GrazeCard:
    name = u'闪'
    image = gres.card_graze
    target = None
    passive_card_prompt = u'你不能主动出闪'

class HealCard:
    # action_stage meta
    target = 'self'
    image = gres.card_heal
    name = u'药'
    #passive_card_prompt = u'xxx'

class DemolitionCard:
    # action_stage meta
    target = 1
    image = gres.card_demolition
    name = u'釜底抽薪'
    #passive_card_prompt = u'xxx'

class RejectCard:
    target = None
    name = u'好人卡'
    image = gres.card_reject
    passive_card_prompt = u'你不能主动出好人卡'

# -----END CARDS UI META-----

# -----BEGIN CHARACTERS UI META-----
__metaclass__ = gen_metafunc(characters)

class Youmu:
    # Character
    name = u'魂魄妖梦'

class Nitoryu:
    # Skill
    name = u'二刀流'

    def clickable(game):
        return False


class Parsee:
    # Character
    name = u'水桥帕露西'

class Envy:
    # Skill
    name = u'嫉妒'

    def clickable(game):
        me = game.me
        print me.stage
        if me.stage == game.ACTION_STAGE and me.cards:
            return True
        return False

class TreatAsDemolition:
    # action_stage meta
    def is_action_valid(source, cards, target_list):
        if len(cards) != 1:
            return (False, u'请选择一张牌！')
        else:
            return Demolition.ui_meta.is_action_valid(source, cards, target_list)


# -----END CHARACTERS UI META-----
