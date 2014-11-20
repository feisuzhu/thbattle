# -*- coding: utf-8 -*-
NONE = 0
BASIC = 0.5
AT = 1
SPEAKER = 2


def _notify(title, msg):
    pass


try:
    import pynotify
    pynotify.init('thbattle')
    n = pynotify.Notification('None')

    def _notify(title, msg):  # noqa
        try:
            n.update(title, msg)
            n.show()
        except:
            pass

except ImportError:
    pass

import os
import platform

if os.name == 'nt' or platform.system() == 'Windows':
    from ctypes import Structure, windll, sizeof, byref
    from ctypes.wintypes import DWORD, HICON, HWND, UINT, WCHAR

    class NOTIFYICONDATAW(Structure):
        _fields_ = [
            ("cbSize", DWORD),
            ("hWnd", HWND),
            ("uID", UINT),
            ("uFlags", UINT),
            ("uCallbackMessage", UINT),
            ("hIcon", HICON),
            ("szTip", WCHAR * 128),
            ("dwState", DWORD),
            ("dwStateMask", DWORD),
            ("szInfo", WCHAR * 256),
            ("uVersion", UINT),
            ("szInfoTitle", WCHAR * 64),
            ("dwInfoFlags", DWORD),
        ]

    NIM_ADD = 0
    NIM_MODIFY = 1
    NIM_DELETE = 2
    NIM_SETFOCUS = 3
    NIM_SETVERSION = 4

    NIF_ICON = 2
    NIF_TIP = 4
    NIF_STATE = 8
    NIF_INFO = 0x10

    NIIF_NONE = 0
    NIIF_INFO = 1
    NIIF_WARNING = 2
    NIIF_ERROR = 3
    NIIF_USER = 4
    NIIF_NOSOUND = 0x10

    GCLP_HICON = -14

    has_init = False

    def _notify(title, msg):  # noqa
        global data, has_init

        if not has_init:
            has_init = True

            from client.ui.base.baseclasses import main_window
            hWnd = main_window._hwnd
            windll.user32.GetClassLongW.restype = HICON
            hIcon = windll.user32.GetClassLongW(hWnd, GCLP_HICON)
            data = NOTIFYICONDATAW(sizeof(NOTIFYICONDATAW), hWnd)
            data.hIcon = hIcon
            data.uFlags = NIF_ICON
            data.uVersion = 3
            windll.shell32.Shell_NotifyIconW(NIM_ADD, byref(data))
            windll.shell32.Shell_NotifyIconW(NIM_SETVERSION, byref(data))
            data.uVersion = 10  # uTimeout
            data.uFlags = NIF_INFO
            data.dwInfoFlags = NIIF_INFO

            def remove_icon():
                windll.shell32.Shell_NotifyIconW(NIM_DELETE, byref(data))
            import atexit
            atexit.register(remove_icon)

        data.szInfoTitle = unicode(title)[:63]
        data.szInfo = unicode(msg)[:255]
        windll.shell32.Shell_NotifyIconW(NIM_MODIFY, byref(data))


def notify(title, msg, level=BASIC):
    from user_settings import UserSettings as us
    if level <= us.notify_level:
        _notify(title, msg)
        if us.sound_notify:
            from client.ui.soundmgr import SoundManager

            SoundManager.play('c-sound-input')

__all__ = ['notify', 'NONE', 'BASIC', 'SPEAKER', 'AT']
