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
AUTOUPDATE_ENABLE = not os.path.exists(os.path.join(UPDATE_BASE, 'NO_UPDATE'))

if not sys.platform.startswith('linux'):
    UPDATE_BASE = os.path.dirname(UPDATE_BASE)

TESTING = os.path.exists(os.path.join(UPDATE_BASE, 'TESTING'))

if TESTING:
    UPDATE_URL = 'http://feisuzhu.xen.prgmr.com/testing/'
else:
    UPDATE_URL = 'http://update.thbattle.net/'

if sys.platform.startswith('linux'):
    UPDATE_URL += 'src/'

VERSION = 'THBATTLE V1.0b incr 56'

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

import re

UPDATE_IGNORES = re.compile(r'''
          ^current_version$
        | ^update_info\.json$
        | ^client_log\.txt$
        | ^.+\.py[co]$
        | ^.*~$
        | ^NO_UPDATE$
        | ^TESTING$
        | ^.*_custom\..{2,4}$
        | ^last_id$
        | ^\.
''', re.VERBOSE)

class ServerList:
    class HakureiShrine:
        address = ('game.thbattle.net', 9998)
        description = (
            u'|R没什么香火钱 博丽神社|r\n\n'
            u'冷清的神社，不过很欢迎大家去玩的，更欢迎随手塞一点香火钱！'
            u'出手大方的话，说不定会欣赏到博丽神社历代传下来的10万元COS哦。\n\n'
            u'|R|B注意：这是测试服务器，并不保证稳定、与正常服务器的同步！|r\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)
        x=893
        y=404

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

NOTICE = u'''
东方符斗祭 测试版
==================

图片素材大多来自于互联网，如果其中有你的作品，请联系我。

虽然显示有3个服务器，但是实际上只有一个。
博丽神社的那个点指向的是自己，所以会连接失败，
请点击另外两个点进入游戏。

|B最近bug修复/加强：|r
各种奇怪的、难以描述的bug
身份场随机座次，大喇叭
某些奇怪的、难以描述的bug
游戏战报窗口，身份场黑幕赢不了的bug
标准身份场
无限好人卡bug修复……
秋穰子 秋祭 技能修改为一回合一次
灵梦灵击恶心丸结算bug修复
灵梦重制，黑白‘借走’的牌放入明牌区

另外，如果提示更新失败，请试着运行一下游戏目录中的update.bat文件更新。

|B游戏论坛：|r
http://www.thbattle.net

论坛有板块接受BUG报告，请附上游戏目录中的client_log.txt文件
|R
游戏QQ群： 175054570
设定讨论群： 247123221（仅讨论设定问题，不是灌水群）
|r
Proton制作
'''.strip()
