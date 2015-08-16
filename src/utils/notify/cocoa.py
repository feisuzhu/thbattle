from pyglet.libs.darwin.cocoapy import ObjCClass, get_NSString, objc, ObjCSubclass

NSUserNotificationCenter = ObjCClass("NSUserNotificationCenter")
NSUserNotification = ObjCClass("NSUserNotification")
NSApplication = ObjCClass("NSApplication")
NSUserNotificationCenterDelegate = objc.objc_getProtocol(bytes("NSUserNotificationCenterDelegate"))

NSApp = NSApplication.sharedApplication()

NotificationDelegateClass = ObjCSubclass('NSObject', 'NotificationDelegate', register=False)
@NotificationDelegateClass.method("v@@")
def userNotificationCenter_didActivateNotification_(self, notificationCenter, notification):
    # bring window to front
    NSApp.activateIgnoringOtherApps_(True)

objc.class_addProtocol(NotificationDelegateClass.objc_cls, NSUserNotificationCenterDelegate)
NotificationDelegateClass.register()
NotificationDelegate = ObjCClass("NotificationDelegate")

notificationCenter = NSUserNotificationCenter.defaultUserNotificationCenter()
notificationCenter.setDelegate_(NotificationDelegate.alloc().init())

def _notify(title, msg):
    notification = NSUserNotification.alloc().init().autorelease()
    notification.setTitle_(get_NSString(title))
    notification.setInformativeText_(get_NSString(msg))
    notificationCenter.deliverNotification_(notification)
