from gevent import Greenlet
from gevent.queue import Queue

class Receptionist(Greenlet):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.queue = Queue(100)
        self.__class__.instance = self

    def _run(self):
        for u in self.queue:
            # TODO: auth / register
            print u.read()

    def recept(self, u):
        self.queue.put(u)
