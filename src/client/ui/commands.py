# -*- coding: utf-8 -*-

from client.ui.base import *
from client.ui.soundmgr import SoundManager

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
        f.argtypes= types
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


@command(u'帮助', u'查看命令的帮助', cmd='?')
@argtypes(str)
@argdesc(u'<命令>')
def help(cmdname):
    cmd = registered_commands.get(cmdname)
    if not cmd:
        return _format_all_commands()
    else:
        help = [cmd.commandname, cmd.commandhelp]
        help.append(u'/%s ' % cmdname + u' '.join(cmd.argdesc))
        return u'\n'.join(help)
