# -*- coding: utf-8 -*-
NONE = 0
BASIC = 0.5
AT = 1
SPEAKER = 2


def _notify(title, msg):
    pass

import os
import platform
import sys

if os.name == 'nt' or platform.system() == 'Windows':
    from .win32 import _notify

elif sys.platform == 'darwin':
    from .cocoa import _notify

else:
    try:
        import pynotify
    except ImportError:
        pass
    else:
        from .pynotify_adapter import _notify

def notify(title, msg, level=BASIC):
    from user_settings import UserSettings as us
    if level <= us.notify_level:
        _notify(title, msg)
        if us.sound_notify:
            from client.ui.soundmgr import SoundManager

            SoundManager.play('c-sound-input')

__all__ = ['notify', 'NONE', 'BASIC', 'SPEAKER', 'AT']
