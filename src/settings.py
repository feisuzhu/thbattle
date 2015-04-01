# -*- coding: utf-8 -*-

from options import options
import sys
import os

__metaclass__ = lambda _1, _2, _dict: _dict.pop('__module__', '..') and _dict


# -- begin settings --
VERSION = 'THBATTLE V1.0b incr 249'

CWD = os.getcwd()
BASEDIR = os.path.dirname(os.path.realpath(__file__))

if sys.platform == 'win32':
    LOGIC_UPDATE_BASE = "src"
    INTERPRETER_UPDATE_BASE = "Python27"
else:
    LOGIC_UPDATE_BASE = BASEDIR
    INTERPRETER_UPDATE_BASE = None

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

ACCOUNT_MODULE = 'freeplay' if options.freeplay else 'forum_integration'
ACCOUNT_FORUMURL = 'http://www.thbattle.net'

TESTING_CHARACTERS = (
)


class ServerNames:
    forum     = u'论坛'
    localhost = u'本机'
    lake      = u'雾之湖'
    forest    = u'魔法之森'
    hakurei   = u'博丽神社'
    aya       = u'文文专访'


def _get_box(vlist):
    xl = [i[0] for i in vlist]
    yl = [i[1] for i in vlist]
    x0, x1 = min(xl) - 5, max(xl) + 10
    y0, y1 = min(yl) - 5, max(yl) + 10
    return x0, y0, x1 - x0, y1 - y0


class ServerList:
    import os
    IS_PROTON = hasattr(os, 'uname') and ''.join(os.uname()).startswith('LinuxProton')
    del os

    class hakurei:
        address = ('cngame.thbattle.net', 8999)
        branch = 'origin/testing'
        polygon = [
            (878, 423), (829, 409), (760, 376), (748, 346), (787, 329),
            (863, 313), (929, 322), (970, 330), (992, 366), (968, 399),
        ]
        box = _get_box(polygon)
        description = (
            u'|R没什么香火钱 博丽神社|r\n\n'
            u'冷清的神社，不过很欢迎大家去玩的，更欢迎随手塞一点香火钱！'
            u'出手大方的话，说不定会欣赏到博丽神社历代传下来的10万元COS哦。\n\n'
            u'|R|B注意：这是测试服务器，并不保证稳定、与正常服务器的同步！|r\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)

    if options.freeplay or IS_PROTON:
        class localhost:
            address = ('127.0.0.1', 9999)
            branch = 'HEAD'
            update_url = None
            polygon = [
                (891, 704), (839, 707), (740, 601), (749, 575), (834, 570),
                (947, 576), (986, 597), (991, 675), (964, 696),
            ]
            box = _get_box(polygon)
            description = (
                u'|R你自己的本机服务器|r'
            )

    class lake:
        address = ('cngame.thbattle.net', 9999)
        branch = 'origin/production'
        polygon = [
            (569, 510), (514, 501), (489, 474), (514, 449), (585, 439),
            (647, 447), (670, 457), (671, 487), (628, 504),
        ]
        box = _get_box(polygon)
        description = (
            u'|R这里没有青蛙 雾之湖|r\n\n'
            u'一个让人开心的地方。只是游客普遍反应，游玩结束后会感到自己的智商被拉低了一个档次。'
            u'另外，请不要把青蛙带到这里来。这不是规定，只是一个建议。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)

    class forest:
        address = ('cngame.thbattle.net', 9999)
        branch = 'origin/production'
        polygon = [
            (360, 415), (237, 380), (197, 309), (222, 199), (285, 159),
            (397, 150), (524, 168), (611, 256), (592, 318), (536, 359),
        ]
        box = _get_box(polygon)
        description = (
            u'|R光明牛奶指定销售地点 魔法之森|r\n\n'
            u'森林里好玩的东西很多，比如被捉弄什么的。'
            u'旁边有一个神奇的物品店，只是店主有点变态。\n\n'
            u'|DB服务器地址： %s|r'
        ) % repr(address)

    del IS_PROTON


NOTICE = u'''
图片素材大多来自于互联网，如果其中有你的作品，请联系我。
Proton制作

|s2ff0000ff|W玩家大多在晚上8点之后进来玩，白天进来没人的话晚上再来试试～|r
|s2ff0000ff|W如果提示更新失败，请试着运行一下游戏目录中的rescue（妖梦图标）更新。|r

|B游戏论坛：|r
http://www.thbattle.net

|B最近更新情况：|r
新人物：河城荷取
人物重做：伊吹萃香
各种bug修复。
----------------------
铃仙：移除了生药的cost
新人物：少名针妙丸
KOF模式调整：选将流程调整、专有牌堆、特别修正的角色
8人身份场调整：黑幕的胜利条件修改为“在城管全部MISS的情况下击坠BOSS”
新人教学模式的对话有配音了（Thanks to VV、君寻、星野樱羽）
白楼剑削弱
一堆bug修复
----------------------
卡图立绘更新、bug修复
----------------------
抢书模式规则微调：持有书增加手牌上限，书可以抵挡致命伤害
bug修复
----------------------
帕秋莉设定微调。
琪露诺重置。
SP八云紫代替了原八云紫，原八云紫乘隙间走了。
bug修复
----------------------
新人物：铃仙
新模式：抢书大作战
东风谷早苗设定调整
移除了没人玩的模式……
|R帐号与论坛绑定，请使用论坛帐号登录游戏！|r
'''.strip()
