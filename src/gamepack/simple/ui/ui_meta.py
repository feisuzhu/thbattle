# -*- coding: utf-8 -*-
from .. import actions
import game
import types

class UiMeta_MetaClass(type):
    def __new__(cls, clsname, bases, _dict):
        meta_for = actions.__dict__.get(clsname)
        assert issubclass(meta_for, game.Action)
        for k, v in _dict.items():
            if isinstance(v, types.FunctionType):
                _dict[k] = staticmethod(v)
        new_cls = type.__new__(cls, clsname + 'UIMeta', (object,) , _dict)
        meta_for.ui_meta = new_cls
        return new_cls

__metaclass__ = UiMeta_MetaClass

# -----BEGIN ACTIONS UI META-----

class Attack:
    # action_stage meta
    target = 1

    def is_action_valid(source, target_list):
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
    target = 'self'

    def is_action_valid(source, target_list):
        target = target_list[0]
        if not source == target:
            return (False, u'BUG!!!!')

        if target.life >= target.maxlife:
            return (False, u'您的体力值已达到上限')
        else:
            return (True, u'嗑一口，精神焕发！')

class UseGraze:
    # choose_card meta
    text_valid = u'我闪！'
    text = u'请出闪...'

class DropCardStage:
    # choose_card meta
    text_valid = u'OK，就这些了'
    text = u'请弃牌...'

# -----END ACTIONS UI META-----
