# -*- coding: utf-8 -*-

# -- stdlib --
from ctypes import Structure, byref, c_uint, c_ushort, c_void_p, c_wchar_p, cast
from ctypes import create_unicode_buffer, pointer, sizeof, windll
import os

# -- third party --
# -- own --
from utils.misc import flatten

# -- code --
HWND = HINSTANCE = DWORD = LPARAM = c_uint
LPOFNHOOKPROC = c_void_p
LPWSTR = c_wchar_p
WORD = c_ushort

OFN_ALLOWMULTISELECT     = 0x00000200
OFN_CREATEPROMPT         = 0x00002000
OFN_DONTADDTORECENT      = 0x02000000
OFN_ENABLEHOOK           = 0x00000020
OFN_ENABLEINCLUDENOTIFY  = 0x00400000
OFN_ENABLESIZING         = 0x00800000
OFN_ENABLETEMPLATE       = 0x00000040
OFN_ENABLETEMPLATEHANDLE = 0x00000080
OFN_EXPLORER             = 0x00080000
OFN_EXTENSIONDIFFERENT   = 0x00000400
OFN_FILEMUSTEXIST        = 0x00001000
OFN_FORCESHOWHIDDEN      = 0x10000000
OFN_HIDEREADONLY         = 0x00000004
OFN_LONGNAMES            = 0x00200000
OFN_NOCHANGEDIR          = 0x00000008
OFN_NODEREFERENCELINKS   = 0x00100000
OFN_NOLONGNAMES          = 0x00040000
OFN_NONETWORKBUTTON      = 0x00020000
OFN_NOREADONLYRETURN     = 0x00008000
OFN_NOTESTFILECREATE     = 0x00010000
OFN_NOVALIDATE           = 0x00000100
OFN_OVERWRITEPROMPT      = 0x00000002
OFN_PATHMUSTEXIST        = 0x00000800
OFN_READONLY             = 0x00000001
OFN_SHAREAWARE           = 0x00004000
OFN_SHOWHELP             = 0x00000010


class OPENFILENAME(Structure):
    _fields_ = [
        ("lStructSize",       DWORD),
        ("hwndOwner",         HWND),
        ("hInstance",         HINSTANCE),
        ("lpstrFilter",       LPWSTR),
        ("lpstrCustomFilter", LPWSTR),
        ("nMaxCustFilter",    DWORD),
        ("nFilterIndex",      DWORD),
        ("lpstrFile",         LPWSTR),
        ("nMaxFile",          DWORD),
        ("lpstrFileTitle",    LPWSTR),
        ("nMaxFileTitle",     DWORD),
        ("lpstrInitialDir",   LPWSTR),
        ("lpstrTitle",        LPWSTR),
        ("flags",             DWORD),
        ("nFileOffset",       WORD),
        ("nFileExtension",    WORD),
        ("lpstrDefExt",       LPWSTR),
        ("lCustData",         LPARAM),
        ("lpfnHook",          LPOFNHOOKPROC),
        ("lpTemplateName",    LPWSTR),
        ("pvReserved",        DWORD),
        ("dwReserved",        DWORD),
        ("flagsEx",           DWORD),
    ]


def _do_open_dlg(func, window, title, filters, flags):
    assert isinstance(title, unicode)

    buf = create_unicode_buffer(1024)
    ofn = OPENFILENAME()

    ofn.lStructSize = sizeof(OPENFILENAME)
    ofn.lpstrFile = cast(pointer(buf), LPWSTR)
    ofn.nMaxFile = 1024
    ofn.lpstrTitle = c_wchar_p(title)
    ofn.flags = flags
    
    if window:
        ofn.hwndOwner = window._hwnd

    filters = flatten(filters) or [u'All files(*.*)', u'*.*']
    assert all([isinstance(i, unicode) for i in filters])
    assert len(filters) % 2 == 0

    filters = u'\0'.join(filters) + u'\0\0'
    ofn.lpstrFilter = c_wchar_p(filters)

    func(byref(ofn))

    rst = buf[:].strip('\0')
    if flags & OFN_ALLOWMULTISELECT:
        return rst.split('\0')
    else:
        return rst


def get_open_file_name(window, title, filters, flags=None):
    flags = flags or OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST | OFN_NOCHANGEDIR
    try:
        wd = os.getcwd()
        return _do_open_dlg(windll.comdlg32.GetOpenFileNameW, window, title, filters, flags)
    finally:
        os.chdir(wd)


def get_save_file_name(window, title, filters, flags=None):
    flags = flags or OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR | OFN_OVERWRITEPROMPT
    try:
        wd = os.getcwd()
        return _do_open_dlg(windll.comdlg32.GetSaveFileNameW, window, title, filters, flags)
    finally:
        os.chdir(wd)
