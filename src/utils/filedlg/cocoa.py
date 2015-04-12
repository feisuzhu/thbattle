from pyglet.libs.darwin.cocoapy import ObjCClass, cfstring_to_string, get_NSString
from ctypes import c_void_p

NSOpenPanel = ObjCClass('NSOpenPanel')
NSSavePanel = ObjCClass('NSSavePanel')
NSArray = ObjCClass('NSArray')


def _get_nsarray(list):
    array = (c_void_p * len(list))()
    for i, v in enumerate(list):
        array[i] = v.ptr

    return NSArray.arrayWithObjects_count_(array, len(array))


def _get_file_name(panel, title, filters):
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(False)
    panel.setAllowsMultipleSelection_(False)
    panel.setTitle_(get_NSString(title))
    
    filters = [get_NSString(f[1][2:]) for f in filters]
    panel.setAllowedFileTypes_(_get_nsarray(filters))
    if panel.runModal():
        return cfstring_to_string(panel.URL().path())


def get_open_file_name(window, title, filters):
    openPanel = NSOpenPanel.openPanel()
    return _get_file_name(openPanel, title, filters)


def get_save_file_name(window, title, filters):
    savePanel = NSSavePanel.savePanel()
    return _get_file_name(savePanel, title, filters)
