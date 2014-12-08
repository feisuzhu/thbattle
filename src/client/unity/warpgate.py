# -*- coding: utf-8 -*-

# -- prioritized --
import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

# -- stdlib --
import random
import traceback

# -- third party --
# -- own --
from game.autoenv import EventHandler
from utils.misc import instantiate


# -- inject --
def inject_static_linked_extensions():
    try:
        import gevent_ares
        import gevent_core
        import gevent_util
        import gevent_semaphore
        import msgpack_packer
        import msgpack_unpacker

        sys.modules['gevent.ares'] = gevent_ares
        sys.modules['gevent.core'] = gevent_core
        sys.modules['gevent._util'] = gevent_util
        sys.modules['gevent._semaphore'] = gevent_semaphore
        sys.modules['msgpack._packer'] = msgpack_packer
        sys.modules['msgpack._unpacker'] = msgpack_unpacker

        import gevent
        import msgpack

        gevent.ares = gevent_ares
        gevent.core = gevent_core
        gevent._util = gevent_util
        gevent._semaphore = gevent_semaphore
        msgpack._packer = msgpack_packer
        msgpack._unpacker = msgpack_unpacker

    except Exception:
        from UnityEngine import Debug
        from traceback import format_exc
        Debug.Log('Inject static extension failed.\n\n' + format_exc())

inject_static_linked_extensions()

# -- after inject --
from gevent.event import Event
import gevent
import gevent.hub


# -- code --
'''
Emits:
    ['game_event', g -> Game, evt_name -> str, arg -> object]  // Game.emit_event
    ['system_event', evt_name -> str, args -> tuple]  // See Executive
'''


class UnityUIEventHook(EventHandler):
    def __init__(self, warpgate, game):
        EventHandler.__init__(self)
        self.warpgate = warpgate
        self.game = game

    def evt_user_input(self, g, evt_name, arg):
        trans, ilet = arg
        evt = Event()
        self.warpgate.events.append(('game_event', self.game, evt_name, (trans, ilet, evt.set)))
        evt.wait()
        return ilet

    def handle(self, evt, data):
        handler = getattr(self, 'evt_' + evt, None)
        if handler:
            handler(self.game, evt, data)
        else:
            self.warpgate.events.append(('game_event', self.game, evt, data))

        if random.random() < 0.1:
            gevent.sleep(0.005)

        return data


@gevent.hub.set_hub
@instantiate
class UnityHub(gevent.hub.Hub):

    def print_exception(self, context, type, value, tb):
        text = ''.join(traceback.format_exception(type, value, tb))
        del tb
        if context is not None:
            if not isinstance(context, str):
                try:
                    context = self.format_context(context)
                except:
                    text += 'Error formatting context\n' + traceback.format_exc()
                    context = repr(context)
            text += ('\n%s failed with %s\n\n' % (context, getattr(type, '__name__', 'exception'), ))

        try:
            from UnityEngine import Debug
            Debug.LogError(text)
        except:
            # fuck
            pass

from gevent.resolver_ares import Resolver
hub = gevent.hub.get_hub()
hub.resolver = Resolver(hub=hub)


class UnityLogStream(object):
    def write(self, data):
        from UnityEngine import Debug
        Debug.Log(data)

import logging
logging.basicConfig(stream=UnityLogStream())
logging.getLogger().setLevel(logging.ERROR)


class ExecutiveWrapper(object):
    def __init__(self, executive, warpgate):
        object.__setattr__(self, "executive", executive)
        object.__setattr__(self, "warpgate", warpgate)

    def __getattr__(self, k):
        return getattr(self.executive, k)

    def __setattr__(self, k, v):
        setattr(self.executive, k, v)

    def connect_server(self, host, port):
        from UnityEngine import Debug
        Debug.Log(repr((host, port)))

        @gevent.spawn
        def do():
            Q = self.warpgate.queue_system_event
            Q('connect', self.executive.connect_server((host, port), Q))

    def start_replay(self, rep):
        self.executive.start_replay(rep, self.warpgate.queue_system_event)

    def update(self):
        Q = self.warpgate.queue_system_event

        def update_cb(name, p):
            Q('update', name, p)

        @gevent.spawn
        def do():
            Q('result', self.executive.update(update_cb))

    def get_account_data(self):
        return self.executive.gamemgr.accdata

    def ignite(self, g):
        g.event_observer = UnityUIEventHook(self.warpgate, g)
        g.start()


@instantiate
class Warpgate(object):

    def init(self):
        import options
        from UnityEngine import Debug

        L = lambda s: Debug.Log("PyWrap: " + s)
        L("init")

        self.events = []

        # should set them
        options.no_update
        options.no_crashreport
        options.show_hidden_mode

        options.freeplay = False

        if options.no_update:
            import autoupdate
            autoupdate.Autoupdate = autoupdate.DummyAutoupdate

        L("before gevent")
        from gevent import monkey
        monkey.patch_socket()
        monkey.patch_os()
        monkey.patch_select()
        L("after gevent")

        from game import autoenv
        autoenv.init('Client')

        import gamepack.thb.ui.ui_meta  # noqa, init ui_meta

        # For debug
        @gevent.spawn
        def beat():
            while True:
                gevent.sleep(1)
                # self.events.append(("tick",))

        from client.core.executive import Executive
        self.executive = ExecutiveWrapper(Executive, self)

    def get_events(self):
        l = self.events
        self.events = []
        return l

    def start_backdoor(self):
        from gevent.backdoor import BackdoorServer
        import gevent
        self.bds = BackdoorServer(('127.0.0.1', 12345))
        self.gr_bds = gevent.spawn(self.bds.serve_forever)

    def stop_backdoor(self):
        self.gr_bds.kill()
        self.bds.close()

    def shutdown(self):
        from client.core.executive import Executive
        if Executive.state == 'connected':
            Executive.disconnect()

    def queue_system_event(self, evt_name, arg=None):
        self.events.append(('system_event', evt_name, arg))
