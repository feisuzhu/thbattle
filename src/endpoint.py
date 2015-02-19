# -*- coding: utf-8 -*-

# -- stdlib --
import json
import logging
import zlib
from collections import deque

# -- third party --
from gevent import coros, socket
import msgpack

# -- own --
# -- code --
log = logging.getLogger("Endpoint")


class EndpointDied(Exception):
    pass


class DecodeError(Exception):
    pass


class Endpoint(object):

    ENDPOINT_DEBUG = False

    FMT_PACKED          = 1
    FMT_BULK_COMPRESSED = 2
    FMT_RAW_JSON        = 3

    def __init__(self, sock, address):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.read       = sock.recv
        sock.write      = sock.sendall

        self.sock       = sock
        self.unpacker   = msgpack.Unpacker(sock, encoding='utf-8')
        self.writelock  = coros.RLock()
        self.address    = address
        self.link_state = 'connected'  # or disconnected
        self.recv_buf   = deque()

    def __repr__(self):
        return '%s:%s:%s' % (
            self.__class__.__name__,
            self.address[0],
            self.address[1],
        )

    @staticmethod
    def encode(p, format=FMT_PACKED):
        def default(o):
            return o.__data__() if hasattr(o, '__data__') else repr(o)

        if format == Endpoint.FMT_PACKED:
            return msgpack.packb([Endpoint.FMT_PACKED, p], default=default, use_bin_type=True)
        elif format == Endpoint.FMT_BULK_COMPRESSED:
            assert isinstance(p, list)
            data = msgpack.packb(p, default=default, use_bin_type=True)
            return msgpack.packb([Endpoint.FMT_BULK_COMPRESSED, zlib.compress(data)], use_bin_type=True)
        elif format == Endpoint.FMT_RAW_JSON:
            return json.dumps(p, default=default)
        else:
            raise Exception('WTF?!')

    @classmethod
    def decode(cls, s):
        return cls.decode_packet(msgpack.unpackb(s, encoding='utf-8'))[1]

    @staticmethod
    def decode_packet(p):
        try:
            if not (isinstance(p, (list, tuple)) and len(p) == 2):
                raise DecodeError

            fmt, data = p
            if fmt == Endpoint.FMT_PACKED:
                return fmt, data
            elif fmt == Endpoint.FMT_BULK_COMPRESSED:
                try:
                    inflated = zlib.decompress(data)
                except Exception:
                    raise DecodeError

                return fmt, msgpack.unpackb(inflated, encoding='utf-8', ext_hook=lambda code, data: None)
            else:
                raise DecodeError
        except (ValueError, msgpack.UnpackValueError):
            raise DecodeError

    def raw_write(self, s):
        if self.link_state == 'connected':
            if Endpoint.ENDPOINT_DEBUG:
                log.debug("SEND>> %s" % self.decode(s))
            try:
                with self.writelock:
                    self.sock.sendall(s)
            except IOError:
                self.close()
        else:
            return False

    def write(self, p, format=FMT_PACKED):
        '''
        Send json encoded packet
        '''
        self.raw_write(self.encode(p, format))

    def close(self):
        if not self.link_state == 'disconnected':
            self.link_state = 'disconnected'
            self.sock.close()

    def read(self):
        if self.link_state != 'connected':
            raise EndpointDied

        if self.recv_buf:
            return self.recv_buf.popleft()

        while True:
            u = self.unpacker
            try:
                try:
                    packet = u.next()
                except msgpack.UnpackValueError:
                    raise DecodeError
                except (StopIteration, IOError):
                    self.close()
                    raise EndpointDied

                fmt, d = self.decode_packet(packet)
                if fmt == Endpoint.FMT_BULK_COMPRESSED:
                    self.recv_buf.extend(d[1:])
                    d = d[0]

                if Endpoint.ENDPOINT_DEBUG:
                    log.debug("<<RECV %r" % d)

                return d

            except DecodeError:
                self.write(['bad_format', None])
                continue
