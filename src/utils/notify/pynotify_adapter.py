import pynotify

pynotify.init('thbattle')
n = pynotify.Notification('None')

def _notify(title, msg):
    try:
        n.update(title, msg)
        n.show()
    except:
        pass
