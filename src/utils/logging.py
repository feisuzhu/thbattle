# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import datetime
import logging
import sys

# -- third party --
from raven.transport.gevent import GeventedHTTPTransport
from raven.handlers.logging import SentryHandler
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


def init(level, sentry_dsn, colored=False):
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
    hdlr.setLevel(getattr(logging, level))
    root.addHandler(hdlr)

    root.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    root.info('==============================================')


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
