import gevent
from gevent import Greenlet
from gevent.queue import Queue

class GameHall(Greenlet):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.queue = Queue(1000)
        self.__class__.instance = self

    def _run(self):
        # TODO: ...
        print 'GameHall: nothing for now'
