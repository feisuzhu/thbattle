# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

# Workaround OpenGL resource recycling issue
import gc
gc.disable()


def start_client():
    import ctypes
    try:
        ctypes.cdll.avbin  # force avbin load
    except:
        pass

    import logging
    import os
    import argparse
    import utils.logging

    parser = argparse.ArgumentParser(prog=sys.argv[0])
    parser.add_argument('--no-update', action='store_true')
    parser.add_argument('--with-gl-errcheck', action='store_true')
    parser.add_argument('--freeplay', action='store_true')
    parser.add_argument('--fastjoin', type=int, default=None)
    parser.add_argument('--dump-gameobj', action='store_true')
    parser.add_argument('--log', default='INFO')
    parser.add_argument('--color-log', action='store_true')
    parser.add_argument('--zoom', type=float, default=1.0)
    parser.add_argument('--show-hidden-modes', action='store_true')

    options = parser.parse_args()

    import options as opmodule
    opmodule.options = options

    IS_PROTON = hasattr(os, 'uname') and os.uname()[:2] == ('Linux', 'Proton')

    import settings
    utils.logging.init(options.log.upper(), settings.SENTRY_DSN, settings.VERSION, IS_PROTON or options.color_log)

    if options.no_update:
        import autoupdate
        autoupdate.Autoupdate = autoupdate.DummyAutoupdate

    log = logging.getLogger('start_client')

    from gevent import monkey
    monkey.patch_socket()
    monkey.patch_os()
    monkey.patch_select()
    monkey.patch_ssl()

    from game import autoenv
    autoenv.init('Client')

    import pyglet

    pyglet.options['shadow_window'] = False

    if not options.with_gl_errcheck:
        pyglet.options['debug_gl'] = False

    from pyglet.gl import gl_info
    if gl_info.get_renderer() == 'GDI Generic':
        ctypes.windll.user32.MessageBoxW(
            0,
            u'你好像没有安装显卡驱动……？这样游戏是跑不起来的。快去安装！',
            u'需要显卡驱动',
            16,
        )
        sys.exit(0)

    if sys.platform.startswith('linux') and options.dump_gameobj:
        import atexit
        import game.base
        atexit.register(game.base.GameObjectMeta._dump_gameobject_hierarchy)
        atexit.register(game.base.EventHandler._dump_eh_dependency_graph)

    from client.ui.entry import start_ui

    # PIL compat
    from PIL import Image
    try:
        Image.frombytes
        Image.Image.tobytes
    except AttributeError:
        log.info('Patching PIL {from,to}bytes')
        Image.frombytes = Image.fromstring
        Image.Image.tobytes = Image.Image.tostring

    # ----------

    try:
        start_ui()
    except KeyboardInterrupt:
        import pyglet
        pyglet.app.exit()
        raise
    except:
        import pyglet
        pyglet.app.exit()

        if options.fastjoin:
            import pdb
            pdb.post_mortem()

        log.exception(u'UI线程崩溃，正在报告bug，请稍等下……')
        from utils.stats import stats
        stats({'event': 'crash'})

        raise


if __name__ == '__main__':
    start_client()
