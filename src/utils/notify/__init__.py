# -*- coding: utf-8 -*-

NONE = 0
BASIC = 0.5
AT = 1
SPEAKER = 2


def _notify(*a, **k):
    # lazy init, mobile platforms needs this
    global _notify

    import os
    import platform
    import sys

    if os.name == 'nt' or platform.system() == 'Windows':
        from .win32 import _notify

    elif sys.platform == 'darwin':
        from .cocoa import _notify

    else:
        try:
            import pynotify  # noqa
        except ImportError:
            _notify = lambda *a, **k: None
        else:
            from .pynotify_adapter import _notify

    return _notify(*a, **k)


def notify(title, msg, level=BASIC):
    from user_settings import UserSettings as us
    if level <= us.notify_level:
        _notify(title, msg)
        if us.sound_notify:
            from client.ui.soundmgr import SoundManager

            SoundManager.play('c-sound-input')


__all__ = ['notify', 'NONE', 'BASIC', 'SPEAKER', 'AT']
