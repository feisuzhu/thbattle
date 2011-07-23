from server.core import Game, EventHandler, Action, GameError
import gevent

class DummyGame(Game):
    name = 'A Dummy Game'
    n_persons = 3
    def game_start(self):
        for i in xrange(3):
            print 'TICK %d' % i
            for p in self.players:
                p.write(['this is a dummy game! you are %s' % repr(self.players)])
            gevent.sleep(1)
