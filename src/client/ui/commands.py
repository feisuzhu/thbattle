# -*- coding: utf-8 -*-

from client.ui.soundmgr import SoundManager
from client.core import Executive
import gevent
import logging

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

        if len(al) != len(cmd.argdesc):
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


@command(u'设置音量', u'音量可以是 on、off 和 0-100 之间的整数')
@argtypes(str)
@argdesc(u'<音量>')
def vol(val):
    if val == 'on':
        val = 100
    elif val == 'off':
        val = 0
    elif val.isdigit():
        val = min(int(val), 100)
        val = max(val, 0)
    else:
        return registered_commands['?']('vol')

    if not val:
        SoundManager.mute()
        return u'已静音。'
    else:
        SoundManager.unmute()
        SoundManager.set_volume(val / 100.0)
        return u'音量已设置为 %d' % val


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
    Executive.call('kick_observer', None, uid)
    return u'指令已发出'


@command(u'报告bug', u'遇到错误时，你可以用此命令主动报告bug')
@argtypes()
@argdesc()
def bugreport():
    from __main__ import do_crashreport
    log.info('Actively filed bug report')
    gevent.spawn(do_crashreport, active=True)
    return u'已经发送了bug报告'

@command(u'开启/关闭游戏邀请', u'on      开启邀请\noff     关闭邀请')
@argtypes(str)
@argdesc(u'<on||off>')
def invite(onoff):
    from user_settings import UserSettings as us
    if onoff == 'on':
        us.no_invite = False
        return u'邀请已开启，之后可以再次收到邀请'
    elif onoff == 'off':
        us.no_invite = True
        return u'邀请已关闭，之后不会再收到邀请'
    else:
        return registered_commands['?']('invite')
