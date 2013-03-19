# -*- coding: utf-8 -*-

from client.ui.base import *

registered_commands = {}

def command(name, help, cmd=None):
    def decorate(f):
        f.commandname = name
        f.commandhelp = help
        try:
            f.framearg
        except:
            f.framearg = False
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


def required(f):
    def wrapper(arg):
        return f(arg), True

    return wrapper


def optional(f, default = None):
    def wrapper(arg = None):
        try:
            if arg is not None:
                return f(arg), True
        except:
            pass
        
        return default, False

    return wrapper


def matchs(regex, f = str):
    import re
    r = re.compile(regex)
    def wrapper(arg):
        if r.match(arg):
            return f(arg)
        else:
            raise ValueError

    return wrapper


def framearg(f):
    f.framearg = True
    return f


def _format_all_commands():
    return '\n'.join([
        u'/%s ' % cmdname + cmd.commandname
        for cmdname, cmd in registered_commands.items()
    ])

def process_command(arglist, frame):
    def process():
        if not arglist: return help()
        
        cmdname = arglist[0]
        cmd = registered_commands.get(cmdname)
        if not cmd: return help()

        al = []

        try:
            i, l = 1, len(arglist)
            for arg in cmd.argtypes:
                v, n = arg(arglist[i]) if i < l else arg()
                al.append(v)
                if n: i += 1

            if i != l:
                raise ValueError
        except:
            return help(cmdname)

        return cmd(*al, frame = frame) if cmd.framearg else cmd(*al)

    msg = process()
    if msg: return u'|R%s|r\n' % msg

# -----------------------------------

@command(u'显示/设置音量', u'音量可以是 on、off、show 或 0-100 之间的整数')
@argtypes(
    optional(matchs(r'se|bgm|all'), 'all'),
    optional(matchs(r'[0-9]+|on|off|show'), 'show')
)
@argdesc(u'[se||bgm||all]', u'[<音量>]')
def vol(kind, val):
    from client.ui.soundmgr import SoundManager as sm
    
    mute = None
    kinds = ('se', 'bgm') if kind == 'all' else (kind,)

    if val == 'on':
        mute = False
    elif val == 'off':
        mute = True
    elif val == 'show':
        def vol(kind):
            kind = 'se_' if kind == 'se' else ''
            muted = u'(静音)' if getattr(sm, kind + 'muted') else ''
            return '%d%s' % (getattr(sm, kind+'volume') *100, muted)

        return '\n'.join([k + u'音量：' + vol(k) for k in kinds])

    elif val.isdigit():
        vol = min(int(val), 100)
        vol = max(vol, 0)

    if mute is not None:
        for k in kinds: sm.mute(mute, k)
        return u'已静音。' if mute else u'静音已解除。'
    else:
        vol /= 100.0
        for k in kinds:
            sm.mute(False, k)
            sm.set_volume(vol, k)
        return u'音量已设置为 %s' % val

@command(u'清屏', u'清空消息框')
@argtypes()
@argdesc()
@framearg
def cls(frame):
    frame.cls()

@command(u'帮助', u'查看命令的帮助', cmd='?')
@argtypes(optional(str))
@argdesc(u'<命令>')
def help(cmdname = None):
    cmd = registered_commands.get(cmdname)
    if not cmd:
        return _format_all_commands()
    help = [cmd.commandname, cmd.commandhelp]
    help.append(u'/%s ' % cmdname + u' '.join(cmd.argdesc))
    return u'\n'.join(help)
