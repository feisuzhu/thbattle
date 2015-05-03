from pyglet.libs.darwin.cocoapy import ObjCClass, get_NSString

NSUserNotificationCenter = ObjCClass("NSUserNotificationCenter")
NSUserNotification = ObjCClass("NSUserNotification")

def _notify(title, msg):
    notificationCenter = NSUserNotificationCenter.defaultUserNotificationCenter()
    notification = NSUserNotification.alloc().init().autorelease()
    notification.setTitle_(get_NSString(title))
    notification.setInformativeText_(get_NSString(msg))
    notificationCenter.deliverNotification_(notification)
