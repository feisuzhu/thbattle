# -*- coding: utf-8 -*-

def makedict(clsname, bases, _dict):
    try:
        del _dict['__module__']
    except KeyError:
        pass

    return _dict

#__metaclass__ = lambda clsname, bases, _dict: _dict
__metaclass__ = makedict

import os

import sys
UPDATE_BASE = os.path.dirname(os.path.realpath(__file__))

if not sys.platform.startswith('linux'):
    UPDATE_BASE = os.path.dirname(UPDATE_BASE)

from options import options

if options.testing:
    UPDATE_URL = 'http://feisuzhu.xen.prgmr.com/testing/'
else:
    UPDATE_URL = 'http://update.thbattle.net/'

if sys.platform.startswith('linux'):
    UPDATE_URL += 'src/'

VERSION = 'THBATTLE V1.0b incr 109'

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

ACCOUNT_MODULE = 'freeplay' if options.freeplay else 'forum_integration'

import re

UPDATE_IGNORES = re.compile(r'''
          ^current_version$
        | ^update_info\.json$
        | ^client_log\.txt$
        | ^.+\.py[co]$
        | ^.*~$
        | ^.*_custom\..{2,4}$
        | ^user_settings.json$
        | ^cc?$
        | ^[sd]$
        | ^\.
''', re.VERBOSE)

class ServerList:
    import os
    IS_PROTON = hasattr(os, 'uname') and os.uname()[:2] == ('Linux', 'Proton')
    del os

    if options.testing or IS_PROTON:
        class HakureiShrine:
            address = ('game.thbattle.net', 8999)
            description = (
                u'|R没什么香火钱 博丽神社|r\n\n'
                u'冷清的神社，不过很欢迎大家去玩的，更欢迎随手塞一点香火钱！'
                u'出手大方的话，说不定会欣赏到博丽神社历代传下来的10万元COS哦。\n\n'
                u'|R|B注意：这是测试服务器，并不保证稳定、与正常服务器的同步！|r\n\n'
                u'|DB服务器地址： %s|r'
            ) % repr(address)
            x=893
            y=404

    if options.freeplay:
        class YourMachine:
            address = ('127.0.0.1', 9999)
            description = (
                u'|R你自己的本机服务器|r'
            )
            x=893
            y=504

    class LakeOfFog:
        address = ('game.thbattle.net', 9999)
        description = (
            u'|R这里没有青蛙 雾之湖|r\n\n'
            u'一个让人开心的地方。只是游客普遍反应，游玩结束后会感到自己的智商被拉低了一个档次。'
            u'另外，请不要把青蛙带到这里来。这不是规定，只是一个建议。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=570
        y=470

    class ForestOfMagic:
        address = ('game.thbattle.net', 9999)
        description = (
            u'|R光明牛奶指定销售地点 魔法之森|r\n\n'
            u'森林里好玩的东西很多，比如被捉弄什么的。'
            u'旁边有一个神奇的物品店，只是店主有点变态。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=379
        y=286

    del IS_PROTON

NOTICE = u'''
东方符斗祭 测试版
==================

图片素材大多来自于互联网，如果其中有你的作品，请联系我。
Proton制作

|R请点击地图上的两个蓝点进入游戏。实际上是同一个服务器。|r
如果提示更新失败，请试着运行一下游戏目录中的update.bat文件更新。

|B游戏论坛：|r
http://www.thbattle.net

|B最近更新情况：|r
莫名其妙卡顿bug修复
异变模式。
早苗设定调整，各种bug修复……
bug修复，复制/粘贴支持（感谢zhyk提供补丁）
修复一处导致服务器卡顿的bug
阳伞设定调整，bug修复，细节调整
霍青娥技能调整，bug修复，代码重构（可能会引入较多的新bug）
|R帐号与论坛绑定，请使用论坛帐号登录游戏！|r
'''.strip()
