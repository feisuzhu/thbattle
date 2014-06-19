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
    UPDATE_URL = 'http://misc.thbattle.net/testing/'
else:
    UPDATE_URL = 'http://update.thbattle.net/'

if sys.platform.startswith('linux'):
    UPDATE_URL += 'src/'

VERSION = 'THBATTLE V1.0b incr 203'

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

ACCOUNT_MODULE = 'freeplay' if options.freeplay else 'forum_integration'
ACCOUNT_FORUMURL = 'http://www.thbattle.net'

import re

UPDATE_IGNORES = re.compile(r'''^(
          current_version
        | .*_custom\..{2,4}
        | .*~
        | .+\.py[co]
        | OGLdpf\.log
        | [sd]
        | \..*
        | \.txt
        | cc?
        | client_log\.txt
        | client_log\.txt\.gz
        | update_info\.json
        | user_settings\.json
    )$
''', re.VERBOSE)


class ServerNames:
    forum = u'论坛'
    localhost = u'本机'
    lake = u'雾之湖'
    forest = u'魔法之森'
    hakurei = u'博丽神社'
    aya = u'文文专访'


def _get_box(vlist):
    xl = [i[0] for i in vlist]
    yl = [i[1] for i in vlist]
    x0, x1 = min(xl) - 5, max(xl) + 10
    y0, y1 = min(yl) - 5, max(yl) + 10
    return x0, y0, x1 - x0, y1 - y0


class ServerList:
    import os
    IS_PROTON = hasattr(os, 'uname') and os.uname()[:2] == ('Linux', 'Proton')
    del os

    if options.testing or IS_PROTON:
        class hakurei:
            address = ('game.thbattle.net', 8999)
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
东方符斗祭 测试版
==================

图片素材大多来自于互联网，如果其中有你的作品，请联系我。
Proton制作

|s2ff0000ff|W玩家大多在晚上8点之后进来玩，白天进来没人的话晚上再来试试～|r
|s2ff0000ff|W如果提示更新失败，请试着运行一下游戏目录中的update.bat文件更新。|r

|B游戏论坛：|r
http://www.thbattle.net

|B最近更新情况：|r
新人物：射命丸文（画师：渚FUN）、SP八云紫（画师：Vivicat From 东方梦斗符）（开发：zhyk）
修复了与八云紫移动伊吹瓢相关的bug
天子、梅蒂欣、妹红、正邪、橙：技能、设定调整
妖梦技能调整：觉醒技效果并入二刀流
爱丽丝重制，技能调整
犬走椛相关bug修复
紫设定调整：跳判定不再能弃置判定牌
小町设定调整：觉醒不再回复残机
灵梦设定调整：取消【纳奉】技能
新人物：梅蒂欣（开发：zhyk）
----
新人物：鬼人正邪、八坂神奈子（开发：zhyk）
新头像：帕秋莉（画师：渚FUN）
大狸子现在在除了KOF之外的所有模式可用
大狸子相关bug修复
新人物：大狸子（人物设计：鵺子丶爱丽丝）
新人物：秦心（画师：Takibi）
新模式：信（xue）仰（zhan）之（dao）战（di）
妖梦设定调整：如果装备了两把武器，现在可以主动弃置一把
好人卡bug修复
人物强度调整（露米娅、早苗、灵梦，具体调整请看论坛帖子）
新人物：藤原妹红(开发：zhyk)
出牌时间调整为25秒
新头像（小町、八意永琳、大妖精、八云紫，画师：渚FUN）
|R帐号与论坛绑定，请使用论坛帐号登录游戏！|r
'''.strip()
