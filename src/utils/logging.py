# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import logging
import sys

# -- third party --
from raven.transport.gevent import GeventedHTTPTransport
from raven.handlers.logging import SentryHandler
import gevent
import raven

# -- own --

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
        except:
            # fuck
            pass


class ServerLogFormatter(logging.Formatter):
    def __init__(self, with_gr_name=True):
        logging.Formatter.__init__(self)
        self.with_gr_name = with_gr_name

    def format(self, rec):

        if rec.exc_info:
            s = []
            s.append('>>>>>>' + '-' * 74)
            s.append(self._format(rec))
            import traceback
            s.append(u''.join(traceback.format_exception(*rec.exc_info)).strip())
            s.append('<<<<<<' + '-' * 74)
            return u'\n'.join(s)
        else:
            return self._format(rec)

    def _format(self, rec):
        from game.autoenv import Game
        import time
        try:
            g = Game.getgame()
        except:
            g = gevent.getcurrent()

        if self.with_gr_name:
            gr_name = ' ' + (getattr(g, 'gr_name', None) or repr(g))
        else:
            gr_name = ''

        if rec.args:
            msg = rec.msg % rec.args if isinstance(rec.msg, basestring) else repr((rec.msg, rec.args)),
        else:
            msg = rec.msg

        return u'[%s %s%s] %s' % (
            rec.levelname[0],
            time.strftime('%y%m%d %H:%M:%S'),
            gr_name.decode('utf-8'),
            msg,
        )


def init(level, sentry_dsn, colored=False):
    patch_gevent_hub_print_exception()

    root = logging.getLogger()
    root.setLevel(0)

    hdlr = logging.FileHandler('client_log.txt', encoding='utf-8')
    hdlr.setLevel(logging.INFO)
    root.addHandler(hdlr)

    hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport))
    hdlr.setLevel(logging.ERROR)
    root.addHandler(hdlr)

    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setLevel(getattr(logging, level))

    logging.getLogger('sentry.errors').setLevel(1000)

    if colored:
        from colorlog import ColoredFormatter

        formatter = ColoredFormatter(
            "%(log_color)s%(message)s%(reset)s",
            log_colors={
                'CRITICAL': 'bold_red',
                'ERROR': 'red',
                'WARNING': 'yellow',
                'INFO': 'green',
                'DEBUG': 'blue',
            }
        )
        hdlr.setFormatter(formatter)

    root.addHandler(hdlr)

    root.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    root.info('==============================================')


def init_unity(level, sentry_dsn):
    root = logging.getLogger()
    root.setLevel(0)

    hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport))
    hdlr.setLevel(logging.ERROR)
    root.addHandler(hdlr)

    hdlr = UnityLogHandler()
    hdlr.setLevel(level)
    root.addHandler(hdlr)

    root.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    root.info('==============================================')


def init_server(level, sentry_dsn, logfile, with_gr_name=True):
    patch_gevent_hub_print_exception()

    root = logging.getLogger()
    root.setLevel(level)

    fmter = ServerLogFormatter(with_gr_name=with_gr_name)
    std = logging.StreamHandler(stream=sys.stdout)
    std.setFormatter(fmter)
    root.addHandler(std)

    hdlr = SentryHandler(raven.Client(sentry_dsn, transport=GeventedHTTPTransport))
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
