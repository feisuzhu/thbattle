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

if sys.platform == 'win32':
    UPDATE_BASE = os.path.dirname(UPDATE_BASE)
    UPDATE_URL = 'http://update.thbattle.net/'
else:
    UPDATE_URL = 'http://update.thbattle.net/src/'

VERSION = 'THBATTLE V1.0b incr 46'

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

import re

UPDATE_IGNORES = re.compile(r'''
          ^current_version$
        | ^update_info\.json$
        | ^client_log\.txt$
        | ^.+\.py[co]$
        | ^.*~$
        | ^NO_UPDATE$
        | ^.*_custom\..{2,4}$
        | ^last_id$
        | ^\.
''', re.VERBOSE)

AUTOUPDATE_ENABLE = not os.path.exists(os.path.join(UPDATE_BASE, 'NO_UPDATE'))

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
大酱送牌崩溃修复
某些恼人的小bug……
将ROLL点过程调整到选将之前
某些内部机制调整（如果出现了以前没有的bug，请报告）
萃香无手牌时不能喝装备的bug
勇仪带白楼剑怪力弃恶心丸导致游戏崩溃的bug

另外，如果提示更新失败，请试着运行一下游戏目录中的update.bat文件更新。

|B游戏论坛：|r
www.thbattle.net(接受BUG报告，请附上游戏目录中的client_log.txt文件)
www.touhou.cc/bbs
也可以通过人人的东方Project公共主页、邮箱(feisuzhu@163.com)联系
|R
游戏QQ群： 175054570
设定讨论群： 247123221（仅讨论设定问题，不是灌水群）
|r
Proton制作
'''.strip()
