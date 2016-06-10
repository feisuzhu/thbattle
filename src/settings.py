# -*- coding: utf-8 -*-

from options import options
import sys
import os

__metaclass__ = lambda _1, _2, _dict: _dict.pop('__module__', '..') and _dict


# -- begin settings --
VERSION = 'THBATTLE V1.0b incr 264 testing 17'

CWD = os.getcwd()
BASEDIR = os.path.dirname(os.path.realpath(__file__))
NAME_SERVER = 'thbattle.net'

if sys.platform == 'win32':
    LOGIC_UPDATE_BASE = "src"
    LOGIC_UPDATE_SERVER = "src.envolve.thbattle.net"
    INTERPRETER_UPDATE_BASE = "Python27"
    INTERPRETER_UPDATE_SERVER = "interpreter.envolve.thbattle.net"
elif sys.platform == "darwin":
    LOGIC_UPDATE_BASE = "src"
    LOGIC_UPDATE_SERVER = "src.envolve.thbattle.net"
    INTERPRETER_UPDATE_BASE = "osx-eggs"
    INTERPRETER_UPDATE_SERVER = "osx-eggs.envolve.thbattle.net"
else:
    LOGIC_UPDATE_BASE = BASEDIR
    LOGIC_UPDATE_SERVER = "src.envolve.thbattle.net"
    INTERPRETER_UPDATE_BASE = None
    INTERPRETER_UPDATE_SERVER = None

HALL_NOTICE_URL = 'http://www.thbattle.net/notice.txt'

ACCOUNT_MODULE = 'freeplay' if options.freeplay else 'forum_integration'
ACCOUNT_FORUMURL = 'http://www.thbattle.net'

IS_PROTON = hasattr(os, 'uname') and ''.join(os.uname()).startswith('LinuxProton')

if IS_PROTON:
    # for debug
    LEANCLOUD_APPID = '2h0vs77zmac59mdwimxhndan8ju61kyfdjaenr7o6xs788j3'
    LEANCLOUD_APPKEY = 'qvdgnat506l4gmwwjbwv6qrsiej1uldznmu0gaagk23l928g'
    SENTRY_DSN = 'https://40f57b33d5814213b078a1de139cc270:5dab5dba0fdb4cb98df6c13766637726@sentry.thbattle.net/3'
else:
    LEANCLOUD_APPID = 'zuqyou98gvr3s7z3rnx27n8g8yoqu6lpwtl8jmbnq4mabbyd'
    LEANCLOUD_APPKEY = '6va366frgv69lr28u58g0d2dw42523cvdztjmgho82bepf6x'
    SENTRY_DSN = 'https://3f966ce5d9d34967be39379df0e26279:69245de6617c4357af30ed99f05894db@sentry.thbattle.net/2'

TESTING_CHARACTERS = (
    'Reimu',
    'Momiji',
    'Seiga',
    'Remilia',
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


NOTICE = u'''
图片素材大多来自于互联网，如果其中有你的作品，请联系我。
Proton制作

|s2ff0000ff|W如果更新出现问题，请试着运行一下游戏目录中的rescue（妖梦图标）更新。|r

|B游戏论坛：|r
http://www.thbattle.net

|B最近更新情况：|r
人物调整：SP射命丸文神隐
装备：⑨的翅膀类别修改成“红色UFO”，附带-1效果。
装备：阴阳玉现在会交换判定牌（之前判定牌不会收入手牌）
装备：巫女服的效果现在是之前的西行妖的效果。
装备：西行妖暂时神隐（无可用设计）
装备：新装备“罪袋的头套”
装备：伊吹瓢调整，现在在回合内造成伤害后不会获得酒的效果
BUG修复：娘娘拿到灵梦的灵击无效的问题修复
BUG修复：小伞的惊吓现在不能使用组合技能作为cost（神枪）
新人物：爱丽丝（推重）
其他：大量立绘更新
------
|s2ff0000ff|W现在所有的房间内聊天都会记录日志，请文明游戏，并且不要在聊天中透露敏感信息。黑幕组会根据聊天日志对违规玩家做处罚。|r
'''.strip()
