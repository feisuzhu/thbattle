# -*- coding: utf-8 -*-

# -- stdlib --
from functools import partial
import logging
import traceback

# -- third party --
from gevent import Timeout
from gevent import socket, Greenlet
from gevent.coros import RLock
import msgpack

# -- own --
from .misc import swallow


# -- code --
REQUEST = 1
RESPONSE = 2
EXCEPTION = 3

log = logging.getLogger('rpc')


class RPCError(Exception):
    pass


class RPCServerGone(RPCError):
    pass


class RPCClient(object):
    def __init__(self, addr, timeout=2):
        self.addr = addr
        self.sock = None
        self.unpacker = None
        self.timeout = timeout
        self.lock = RLock()

    def __getattr__(self, name):
        return partial(self.call, name)

    def call(self, func_name, *args, **kwargs):
        for i in range(2):
            try:
                return self._do_call(func_name, args, kwargs)
            except RPCServerGone:
                pass

        raise RPCError("WTF?! Shouldn't be here!")

    def _do_call(self, func_name, args, kwargs):
        with self.lock:
            if not self.sock:
                try:
                    connected = False
                    with Timeout(self.timeout):
                        s = socket.socket()
                        s.connect(self.addr)
                        connected = True

                    if not connected:
                        raise RPCError("Connection time out!")

                except socket.error:
                    raise RPCError("can't connect!")

                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.read = s.recv
                s.write = s.send
                self.unpacker = msgpack.Unpacker(s)
                self.sock = s

            try:
                msgpack.pack([REQUEST, func_name, args, kwargs], self.sock)
                resp = self.unpacker.unpack()
            except:
                swallow(self.sock.close)()
                self.sock = self.unpacker = None
                raise RPCServerGone()

            if resp[0] == RESPONSE:
                # resp == [RESPONSE, result]
                return resp[1]
            elif resp[0] == EXCEPTION:
                # resp == [EXCEPTION, name, traceback_text]
                exc = RPCError('Remote exception: %s' % resp[1])
                exc.traceback_text = resp[2]
                raise exc

            raise RPCError('Wrong protocol!')


class RPCService(Greenlet):
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        Greenlet.__init__(self)

    def _run(self):
        try:
            sock = self.sock
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.read = sock.recv
            sock.write = sock.send
            unpacker = msgpack.Unpacker(sock)
            for req in unpacker:
                if not req[0] == REQUEST:
                    msgpack.pack([EXCEPTION, 'InvalidRequest', ''], sock)
                    continue

                _, method, args, kwargs = req
                f = getattr(self, method, None)

                if not f:
                    log.error('Calling undefined method %s.%s', self.__class__.__name__, method)
                    msgpack.pack([EXCEPTION, 'NoSuchMethod', ''], sock)
                    continue

                try:
                    ret = f(*args, **kwargs)
                    log.info('Calling method %s.%s success', self.__class__.__name__, method)
                    rst = [RESPONSE, ret]
                except Exception as e:
                    log.exception('Calling method %s.%s FAIL', self.__class__.__name__, method)
                    rst = [EXCEPTION, e.__class__.__name__, traceback.format_exc()]

                msgpack.pack(rst, sock)

        except:
            swallow(sock.close)()
