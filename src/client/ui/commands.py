# -*- coding: utf-8 -*-

# -- stdlib --
import logging

# -- third party --

# -- own --
from client.core import Executive
from utils.stats import stats

# -- code --
log = logging.getLogger('commands')
registered_commands = {}


def command(name, help, cmd=None):
    def decorate(f):
        f.commandname = name
        f.commandhelp = help
        registered_commands[cmd or f.__name__] = f
        return f

    return decorate


def argdesc(*desclist):
    def decorate(f):
        f.argdesc = desclist
        return f

    return decorate


def argtypes(*types):
    def decorate(f):
        f.argtypes = types
        return f

    return decorate


def _format_all_commands():
    return '\n'.join([
        u'/%s ' % cmdname + cmd.commandname
        for cmdname, cmd in registered_commands.items()
    ])


def process_command(arglist):
    while True:
        if not arglist:
            prompt = _format_all_commands()
            break

        al = list(arglist)
        cmdname = al.pop(0)
        cmd = registered_commands.get(cmdname)
        if not cmd:
            prompt = _format_all_commands()
            break

        if not al and cmdname == '?':
            prompt = u'\n'.join((cmd(None), cmd('?')))
            break

        if len(al) != len(cmd.argtypes):
            prompt = registered_commands['?'](cmdname)
            break

        try:
            al = [argtype(i) for argtype, i in zip(cmd.argtypes, al)]
        except:
            prompt = registered_commands['?'](cmdname)
            break

        prompt = cmd(*al)
        break

    return u'|R%s|R\n' % prompt

# -----------------------------------


@command(u'设置提醒显示级别', u'off     禁用提醒\nbasic   启用基本提醒\nat      启用@提醒\nspeaker 为文文新闻显示提醒\nsound   启用声音提醒\nnosound 禁用声音提醒')
@argtypes(str)
@argdesc(u'<off||basic||at||speaker||sound||nosound>')
def notify(val):
    from user_settings import UserSettings as us

    if val == 'sound':
        us.sound_notify = True
        return u'声音提醒已启用。'

    if val == 'nosound':
        us.sound_notify = False
        return u'声音提醒已禁用。'

    from utils.notify import NONE, BASIC, AT, SPEAKER
    try:
        level = {
            'off': NONE, 'basic': BASIC,
            'at': AT, 'speaker': SPEAKER,
        }[val]
    except KeyError:
        return registered_commands['?']('notify')

    us.notify_level = level

    return u'提醒级别已变更为%s。' % val


@command(u'帮助', u'查看命令的帮助', cmd='?')
@argtypes(str)
@argdesc(u'[<命令>]')
def help(cmdname):
    cmd = registered_commands.get(cmdname)
    if not cmd:
        return _format_all_commands()
    else:
        help = [cmd.commandname, cmd.commandhelp]
        help.append(u'/%s ' % cmdname + u' '.join(cmd.argdesc))
        return u'\n'.join(help)


@command(u'踢出观战玩家', u'uid为观战玩家[]中的数字id')
@argtypes(int)
@argdesc(u'<uid>')
def kickob(uid):
    stats({'event': 'kick_ob'})
    Executive.kick_observer(uid)

    # reply by server message later
    return u''


@command(u'开启/关闭游戏邀请', u'on      开启邀请\noff     关闭邀请')
@argtypes(str)
@argdesc(u'<on||off>')
def invite(onoff):
    from user_settings import UserSettings as us
    if onoff == 'on':
        us.no_invite = False
        return u'邀请已开启，其他玩家可以邀请你一起游戏。'
    elif onoff == 'off':
        us.no_invite = True
        return u'邀请已关闭，其他玩家邀请你时会自动拒绝，不会有提示。'
    else:
        return registered_commands['?']('invite')


@command(u'观战', u'只能在大厅内使用，uid为右侧玩家列表中[]内的数字id')
@argtypes(int)
@argdesc(u'<uid>')
def ob(uid):
    Executive.observe_user(uid)
    return u'已经向[%d]发送了旁观请求，请等待回应……' % uid


@command(u'调试用', u'开发者使用的功能，玩家可以忽略')
@argtypes(str, str)
@argdesc(u'<key>', u'<val>')
def dbgval(key, val):
    from utils.misc import dbgvals
    dbgvals[key] = val
    return u'Done'


@command(u'屏蔽用户', u'屏蔽该用户发言')
@argtypes(str)
@argdesc(u'<用户名>')
def block(user):
    from user_settings import UserSettings as us
    blocked_users = us.blocked_users
    if user not in blocked_users:
        blocked_users.append(user)


@command(u'取消屏蔽用户', u'恢复被屏蔽的用户')
@argtypes(str)
@argdesc(u'<用户名>')
def unblock(user):
    from user_settings import UserSettings as us
    blocked_users = us.blocked_users
    if user in blocked_users:
        blocked_users.remove(user)


@command(u'使用物品', u'使用在游戏中的物品（比如选将卡、欧洲卡）')
@argtypes(str)
@argdesc(u'物品名称')
def use(sku):
    from client.core.executive import Executive
    Executive.use_item(sku)
    return u''
