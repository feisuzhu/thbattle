# -*- coding: utf-8 -*-

import sys
import logging
import cStringIO

tee = None
debug_logfile = cStringIO.StringIO()


class DummyStream(object):
    def write(self, data):
        pass


class Tee(object):
    def __init__(self):
        stdout = sys.__stdout__
        # dummy stdout if underlying file not exists
        self.stdout = DummyStream() if stdout.fileno() < 0 else stdout

        self.logfile = f = open('client_log.txt', 'a+')
        self.history = []
        import datetime
        s = (
            '\n' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") +
            '\n==============================================\n'
        )
        self.history.append(s)
        f.write(s)

    def write(self, v):
        self.stdout.write(v)
        self.history.append(v)
        self.logfile.write(v.encode('utf-8'))


def install_tee(level):
    global tee
    tee = sys.stderr = sys.stdout = Tee()

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    hldr = logging.StreamHandler(tee)
    hldr.setLevel(getattr(logging, level))
    root.addHandler(hldr)

    hldr = logging.StreamHandler(debug_logfile)
    hldr.setLevel(logging.DEBUG)
    root.addHandler(hldr)


def _send_crashreport(text, active):
    import requests
    import zlib

    content = zlib.compress(text.encode('utf-8'))

    try:
        from game.autoenv import Game
        g = Game.getgame()
        gameid = g.gameid
    except:
        gameid = 0

    try:
        from client.core import Executive
        userid = Executive.gamemgr.account.userid
        username = Executive.gamemgr.account.username
    except:
        userid = 0
        username = u'unknown'

    requests.post(
        'http://www.thbattle.net/interconnect/crashreport',
        data={
            'gameid': gameid,
            'active': int(active),
            'userid': userid,
            'username': username,
        },
        files={'file': content},
    )


def do_crashreport(active=False):
    import traceback
    s = u''.join(tee.history)
    s += u'\n\n\nException:\n' + '=' * 80 + '\n' + traceback.format_exc()
    import pyglet.info
    s += u'\n\n\nPyglet info:\n' + pyglet.info.dump()
    debug_logfile.seek(0)
    debug_log = debug_logfile.read()
    s += u'\n\n\nDebug log:\n' + '=' * 80 + '\n' + debug_log
    _send_crashreport(s, active)


def do_crashreport_unity(active=False):
    import traceback
    s = u'\n\n\nException:\n' + '=' * 80 + '\n' + traceback.format_exc()
    _send_crashreport(s, active)
