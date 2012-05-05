# -*- coding: utf-8 -*-

def makedict(clsname, bases, _dict):
    try:
        del _dict['__module__']
    except KeyError:
        pass

    return _dict

#__metaclass__ = lambda clsname, bases, _dict: _dict
__metaclass__ = makedict

VERSION = 'PROTON NOT COMPLETED 01'
AUTOUPDATE_ENABLE = True

import os

UPDATE_BASE = os.getcwd()
UPDATE_URL = 'http://127.0.0.1:8000/'

class ServerList:
    class HakureiShrine:
        address = ('127.0.0.1', 9999)
        description = (
            u'|R没什么香火钱 博丽神社|r\n\n'
            u'冷清的神社，不过很欢迎大家去玩的，更欢迎随手塞一点香火钱！'
            u'出手大方的话，说不定会欣赏到博丽神社历代传下来的10万元COS哦。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=893
        y=404

    class LakeOfFog:
        address = ('feisuzhu.xen.prgmr.com', 9999)
        description = (
            u'|R这里没有青蛙 雾之湖|r\n\n'
            u'一个让人开心的地方。只是游客普遍反应，游玩结束后会感到自己的智商被拉低了一个档次。'
            u'另外，请不要把青蛙带到这里来。这不是规定，只是一个建议。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=570
        y=470

    class ForestOfMagic:
        address = ('127.0.0.1', 9999)
        description = (
            u'|R光明牛奶指定销售地点 魔法之森|r\n\n'
            u'森林里好玩的东西很多，比如被捉弄什么的。'
            u'旁边有一个神奇的物品店，只是店主有点变态。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=379
        y=286

NOTICE = u'''
东方符斗祭 测试版
==================

仍然有很多bug与不完善的地方。
图片素材大多来自于互联网，如果其中有你的作品，请联系我。

feisuzhu@163.com

Proton制作

'''.strip()
