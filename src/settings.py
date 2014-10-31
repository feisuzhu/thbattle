# -*- coding: utf-8 -*-

from options import options
import sys
import os

__metaclass__ = lambda _1, _2, _dict: _dict.pop('__module__', '..') and _dict


# -- begin settings --
VERSION = 'THBATTLE V1.0b incr 230'

CWD = os.getcwd()
LOGIC_UPDATE_BASE = os.path.relpath(os.path.dirname(os.path.realpath(__file__)), CWD)
INTERPRETER_UPDATE_BASE = None

if sys.platform == 'win32':
    INTERPRETER_UPDATE_BASE = os.path.relpath(os.path.dirname(sys.executable), CWD)

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
|s2ff0000ff|W如果提示更新失败，请试着运行一下游戏目录中的update.bat文件更新。|r

|B游戏论坛：|r
http://www.thbattle.net

|B最近更新情况：|r
Replay功能上线！
新人物：东风谷早苗（推重）、八坂神奈子（推重）
卡牌/人物配音：感谢 VV、shourei小N、大白、君寻、小羽、简翎、北斗夜、小舞 帮助配音，感谢 相沢加奈 在早期所作的支持和推动。
使用技能弃置恶心丸时，立即触发恶心丸效果。
风见幽香bug修复
新人物：SP芙兰朵露
旧人物推重：风见幽香
身份场双黑幕模式
更容易的测试服务器切换
新模式：2v2
KOF模式加入“允许不平衡角色”选项
信仰争夺战、异变模式现在可以选择随机/固定座位阵营
勋章系统
射命丸文技能调整
新人物：射命丸文（画师：渚FUN）、SP八云紫（画师：Vivicat From 东方梦斗符）（开发：zhyk）
|R帐号与论坛绑定，请使用论坛帐号登录游戏！|r
'''.strip()
