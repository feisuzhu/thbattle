# -*- coding: utf-8 -*-

# -- prioritized --
import sys
sys.path.append('../src')
from game import autoenv
from game_test import Game, user_input
autoenv.init('Test', {
    'G': Game,
    'U': user_input
})

import options
import logging
import gevent

MAIN = gevent.getcurrent()


class ServerLogFormatter(logging.Formatter):
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

        gr_name = getattr(g, 'gr_name', None) or repr(g)
        gr_name = 'MAIN' if g is MAIN else gr_name

        return u'[%s %s %s] %s' % (
            rec.levelname[0],
            time.strftime('%y%m%d %H:%M:%S'),
            gr_name.decode('utf-8'),
            rec.msg % rec.args if isinstance(rec.msg, basestring) else repr((rec.msg, rec.args)),
        )

fmter = ServerLogFormatter()

root = logging.getLogger()

root.setLevel(logging.WARN)
std = logging.StreamHandler(stream=sys.stdout)
std.setFormatter(fmter)
root.handlers = []
root.addHandler(std)


class Options(object):
    testing = True
    freeplay = True

options.options = Options()
import unittest

tests = unittest.defaultTestLoader.discover('characters')

if __name__ == '__main__':
    unittest.TextTestRunner().run(tests)
