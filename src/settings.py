# -*- coding: utf-8 -*-

from options import options
import sys
import os

__metaclass__ = lambda _1, _2, _dict: _dict.pop('__module__', '..') and _dict


# -- begin settings --
VERSION = 'V265'

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
    'Youmu',
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
|s2ff0000ff|W现在所有的房间内聊天都会记录日志，请文明游戏，并且不要在聊天中透露敏感信息。黑幕组会根据聊天日志对违规玩家做处罚。|r

|B最近更新情况：|r
平衡性调整：
早苗/神裔  效果由原来的2选1变成了重铸一张牌，并修复了之前其发动时机不正确的问题
正邪/挑拨  目标角色无法再指定自己为弹幕的目标，同时因为该削弱，我们暂时将正邪移出了 KOF 模式，尽请期待其 KOF 专属设定的出现。
水桥/嫉妒  规范了回收方块牌效果发动的时机和 cost，现在你不需要将城管执法进行转化亦可触发该效果。
黑兔子     由于其对新人/非洲酋长不友好的原因，我们将其暂时移出了 KOF 模式。
罪袋的头套 触发的判定条件调整为和罪袋一致。
针妙丸/付丧神之怨 时机调整为失去装备区的牌后发动，现在重铸不能再触发该技能了

重做了博丽灵梦和犬走椛的技能。

新元素：
BOSS技：在身份模式下，BOSS可以从几个固定技能里选择一个，并作为自己本局游戏的BOSS技了。
另外有少部分角色拥有自己的专属BOSS技，比如大小姐和灵梦，她们也会以专属BOSS的身份出现在BOSS的固定选将里。

干劲：我们引入了这个新的机制，来代替之前“使用弹幕次数限制”的概念
即从之前的“出牌阶段限使用一次弹幕”改为“出牌阶段使用弹幕需要消耗一点干劲”（默认情况下，每个出牌阶段你只有一点干劲）
同理，它也将作为一些其它技能的 cost（比如魔导书）。

武器重铸：为武器增加了重铸的选项。现在你可以选择是重铸或是装备一把武器了。该选项需要消耗一点干劲。

更新了大量的立绘，现在游戏里的所有立绘的版权均为符斗祭所有。
更新了大部分角色的描述，使其更规范和易于理解。
修复了部分bug。

查看详细：http://www.thbattle.net/thread-36166-1-1.html

论坛：www.thbattle.net 贴吧：东方符斗祭吧 玩家群： 244369953（较热闹的水群）296820759（萌新群）
大型幻想对撞机 & 丝风 Presents
'''.strip()
