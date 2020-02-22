# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any
import datetime
import logging
import sys

# -- third party --
from raven.handlers.logging import SentryHandler
from raven.transport.gevent import GeventedHTTPTransport
import gevent
import raven

# -- own --
from utils.escapes import escape_codes


# -- code --
class UnityLogHandler(logging.Handler):

    def emit(self, rec):
        msg = self.format(rec)

        try:
            from UnityEngine import Debug
            if rec.levelno <= logging.DEBUG:
                Debug.LogDebug(msg)
            elif rec.levelno <= logging.INFO:
                Debug.LogInfo(msg)
            elif rec.levelno <= logging.ERROR:
                Debug.LogError(msg)
            else:
                Debug.LogError(msg)
        except Exception:
            # fuck
            pass


class _ServerLogFormatter_OLD(logging.Formatter):
    def __init__(self, with_gr_name=True):
        logging.Formatter.__init__(self)
        self.with_gr_name = with_gr_name

    def format(self, rec):

        if rec.exc_info:
            s = []
            s.append('>>>>>>' + '-' * 74)
            s.append(self._format(rec))
            import traceback
            s.append(''.join(traceback.format_exception(*rec.exc_info)).strip())
            s.append('<<<<<<' + '-' * 74)
            return '\n'.join(s)
        else:
            return self._format(rec)

    def _format(self, rec):
        import time
        g = gevent.getcurrent()

        if self.with_gr_name:
            gr_name = ' ' + getattr(g, 'gr_name', repr(g))
        else:
            gr_name = ''

        if rec.args:
            msg = (rec.msg % rec.args) if isinstance(rec.msg, str) else repr((rec.msg, rec.args))
        else:
            msg = rec.msg

        return '[%s %s%s] %s' % (
            rec.levelname[0],
            time.strftime('%y%m%d %H:%M:%S'),
            gr_name,
            msg,
        )


class ServerLogFormatter(logging.Formatter):
    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color
        self.color_mapping = {
            'CRITICAL': 'bold_red',
            'ERROR': 'red',
            'WARNING': 'yellow',
            'INFO': 'green',
            'DEBUG': 'blue',
        }

    def format(self, rec):

        if rec.exc_info:
            s = []
            s.append('>>>>>>' + '-' * 74)
            s.append(self._format(rec))
            import traceback
            s.append(''.join(traceback.format_exception(*rec.exc_info)).strip())
            s.append('<<<<<<' + '-' * 74)
            return '\n'.join(s)
        else:
            return self._format(rec)

    def _format(self, rec):
        import time
        g = gevent.getcurrent()
        gr_name = getattr(g, 'gr_name', None)
        if not gr_name:
            if isinstance(g, gevent.Greenlet):
                gr_name = repr(g)
            else:
                gr_name = '<RAW>'

        rec.message = rec.getMessage()
        lvl = rec.levelname
        prefix = '[{} {} {}:{} {}]'.format(
            lvl[0],
            time.strftime('%y%m%d %H:%M:%S'),
            rec.module,
            rec.lineno,
            gr_name,
        )
        if self.use_color:
            E = escape_codes
            M = self.color_mapping
            prefix = f"{E[M[lvl]]}{prefix}{E['reset']}"

        return f'{prefix} {rec.message}'


def init(level, sentry_dsn, release):
    patch_gevent_hub_print_exception()

    root = logging.getLogger()
    root.setLevel(0)

    hdlr: Any

    hdlr = logging.FileHandler('client_log.txt', encoding='utf-8')
    hdlr.setLevel(logging.INFO)
    root.addHandler(hdlr)

    if sentry_dsn:
        hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport, release=release))
        hdlr.setLevel(logging.ERROR)
        root.addHandler(hdlr)

    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setLevel(getattr(logging, level))

    logging.getLogger('sentry.errors').setLevel(1000)

    formatter = ServerLogFormatter()
    hdlr.setFormatter(formatter)
    root.addHandler(hdlr)

    root.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    root.info('==============================================')


def init_unity(level, sentry_dsn, release):
    root = logging.getLogger()
    root.setLevel(0)

    if sentry_dsn:
        hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport, release=release))
        hdlr.setLevel(logging.ERROR)
        root.addHandler(hdlr)

    hdlr = UnityLogHandler()
    hdlr.setLevel(level)
    root.addHandler(hdlr)

    root.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    root.info('==============================================')


def init_server(level, sentry_dsn, release, logfile, with_gr_name=True):
    patch_gevent_hub_print_exception()

    root = logging.getLogger()
    root.setLevel(level)

    fmter = ServerLogFormatter()
    std = logging.StreamHandler(stream=sys.stdout)
    std.setFormatter(fmter)
    root.addHandler(std)

    if sentry_dsn:
        hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport, release=release))
        hdlr.setLevel(logging.ERROR)
        root.addHandler(hdlr)

    logging.getLogger('sentry.errors').setLevel(1000)

    if logfile:
        from logging.handlers import WatchedFileHandler
        filehdlr = WatchedFileHandler(logfile)
        filehdlr.setFormatter(fmter)
        root.addHandler(filehdlr)


def patch_gevent_hub_print_exception():
    from gevent.hub import Hub

    def print_exception(self, context, type, value, tb):
        import logging
        log = logging.getLogger('exception')
        log.error(
            '%s failed with %s',
            context, getattr(type, '__name__', 'exception'),
            exc_info=(type, value, tb),
        )

    Hub.print_exception = print_exception
