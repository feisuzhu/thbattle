# -*- coding: utf-8 -*-

from client.ui.base import *
from client.core import Executive

def caller():
    import inspect
    frame = inspect.currentframe().f_back.f_back  # caller of caller
    return inspect.getargvalues(frame.f_back).locals['func']

from functools import *
def category(func):
    @wraps(func, WRAPPER_ASSIGNMENTS + WRAPPER_UPDATES, ())
    def wrapper(name = None, *a):
        try:
            func.subcommands
        except AttributeError:
            func.subcommands = {}
            func()
        try:
            command = func.subcommands[name]
        except KeyError:
            commands = func.subcommands.itervalues()
            msg = u'\n'.join(get_help_msg(cmd) for cmd in commands)
            return u'|R{}|r\n'.format(msg)

        try:
            return command(*a)
        except TypeError:
            return u'|R{}|r\n'.format(get_help_msg(command))

    return wrapper

def subcommand(func, parent = None):
    if not parent:
        parent = caller() 
    
    parent.subcommands[func.__name__] = func
    try:
        func.command_name = parent.command_name + ' ' + func.__name__
    except AttributeError:
        func.command_name = '/' + func.__name__
    return func

def subcategory(func):
    func = category(func)
    return subcommand(func, caller())

def get_help_msg(func):
    msg = func.command_name
    
    try:
        arginfo = ' |DB{}|R'.format(func.arginfo)
        msg += arginfo
    except:
        pass
    
    try:
        help_msg = '\t' + func.help_msg
        msg += help_msg
    except:
        pass
    return msg

def help_msg(msg):
    def set_help_msg(func):
        func.help_msg = msg
        return func
    return set_help_msg

def arginfo(msg):
    def set_arginfo(func):
        func.arginfo = msg
        return func
    return set_arginfo

@category
def root():
    @subcategory
    @help_msg(u'背景音乐相关')
    def bgm():
        import soundmgr

        @subcommand
        @help_msg(u'静音')
        def mute():
            soundmgr.mute()
            return u'|RBGM已静音。|r\n'

        @subcommand
        @help_msg(u'取消静音')
        def unmute():
            soundmgr.unmute()
            return u'|RBGM已取消静音。|r\n'
        
        @subcommand
        @arginfo(u'<音量>')
        @help_msg(u'调整bgm音量')
        def vol(percent):
            try:
                vol = float(percent) / 100
                if vol < 0 or vol > 1:
                    raise ValueError
                soundmgr.set_volume(vol)
                return u'|RBGM音量已设置为|DB' + percent + u'|R。|r\n'
            except ValueError:
                return u'|R音量应该在0至100之间。|r\n'

    @subcategory
    @help_msg(u'聊天框相关')
    def chat():
        @subcommand
        @arginfo(u'<数量>')
        @help_msg(u'调整聊天框历史记录最大数量')
        def history(count):
            from screens import ChatBoxFrame
            try:
                c = int(count)
                if c < 0:
                    raise ValueError
                if c:
                    ChatBoxFrame.history = ChatBoxFrame.history[-c:]
                else:
                    ChatBoxFrame.history = []
                ChatBoxFrame.history_limit = int(count)
            except ValueError:
                return u'|R数量应为非负整数。|r\n'
            return u'|R历史记录最到数量已调整为|DB' + count + '|R。|r\n'
