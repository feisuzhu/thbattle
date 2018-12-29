# -*- coding: utf-8 -*-

# -- stdlib --
from enum import IntEnum
from typing import Any, Iterator, Sequence, Tuple, List
import logging
import zlib

# -- third party --
from gevent import socket
from gevent.lock import RLock
from gevent.timeout import Timeout
import msgpack

# -- own --
import wire


# -- code --
log = logging.getLogger("Endpoint")


class EndpointDied(Exception):
    pass


class DecodeError(Exception):
    pass


class Format(IntEnum):
    Packed = 1
    BulkCompressed = 2


class Endpoint(object):

    ENDPOINT_DEBUG = False

    def __init__(self, sock, address):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.read       = sock.recv
        sock.write      = sock.sendall

        self.sock       = sock
        self.unpacker   = msgpack.Unpacker(sock, encoding='utf-8')
        self.writelock  = RLock()
        self.address    = address
        self.link_state = 'connected'  # or disconnected

    def __repr__(self):
        return '%s:%s:%s' % (
            self.__class__.__name__,
            self.address[0],
            self.address[1],
        )

    @staticmethod
    def encode(p: wire.Message) -> bytes:
        return msgpack.packb([Format.Packed, p.encode()], use_bin_type=True)

    @staticmethod
    def encode_bulk(pl: Sequence[wire.Message]) -> bytes:
        data = msgpack.packb([i.encode() for i in pl], use_bin_type=True)
        return msgpack.packb([Format.BulkCompressed, zlib.compress(data)], use_bin_type=True)

    def write(self, p) -> None:
        if Endpoint.ENDPOINT_DEBUG:
            log.debug("SEND>> %s" % p)
        self.raw_write(self.encode(p))

    def write_bulk(self, pl: Sequence[wire.Message]) -> None:
        if Endpoint.ENDPOINT_DEBUG:
            for p in pl:
                log.debug("SEND>> %s" % p)
        self.raw_write(self.encode_bulk(pl))

    def raw_write(self, s: bytes) -> None:
        if self.link_state == 'connected':
            try:
                with self.writelock:
                    self.sock.sendall(s)
            except IOError:
                self.close()

    def close(self):
        if not self.link_state == 'disconnected':
            self.link_state = 'disconnected'
            self.sock.close()

    @staticmethod
    def _decode_packet(p: Any) -> Tuple[Format, Any]:
        try:
            if not (isinstance(p, (list, tuple)) and len(p) == 2):
                raise DecodeError

            fmt, data = p
            fmt = Format(fmt)
            if fmt == Format.Packed:
                return fmt, data
            elif fmt == Format.BulkCompressed:
                try:
                    inflated = zlib.decompress(data)
                except Exception:
                    raise DecodeError

                return fmt, msgpack.unpackb(inflated, encoding='utf-8', ext_hook=lambda code, data: None)
            else:
                raise DecodeError
        except (ValueError, msgpack.UnpackValueError):
            raise DecodeError

    @staticmethod
    def decode_bytes(s: bytes) -> List[wire.Message]:
        p = msgpack.unpackb(s, raw=False)
        fmt, data = Endpoint._decode_packet(p)
        if fmt == Format.Packed:
            msg = wire.Message.decode(data)
            if not msg:
                raise DecodeError
            return [msg]
        elif fmt == Format.BulkCompressed:
            return data

        assert False, 'WTF'

    def messages(self, timeout=90) -> Iterator[wire.Message]:
        if self.link_state != 'connected':
            raise EndpointDied

        unpacker = self.unpacker
        _NONE = object()
        while True:
            try:
                v = _NONE
                with Timeout(timeout, False):
                    v = next(unpacker)

                if v is not _NONE:
                    fmt, data = self._decode_packet(v)
                    if fmt == Format.Packed:
                        msg = wire.Message.decode(data)
                        if msg:
                            if Endpoint.ENDPOINT_DEBUG:
                                log.debug("<<RECV %r" % msg)
                            yield msg
                    elif fmt == Format.BulkCompressed:
                        for d in data:
                            msg = wire.Message.decode(d)
                            if msg:
                                if Endpoint.ENDPOINT_DEBUG:
                                    log.debug("<<RECV %r" % msg)
                                yield msg
                else:
                    self.close()
                    raise EndpointDied

            except DecodeError:
                continue

            except msgpack.UnpackValueError:
                continue
