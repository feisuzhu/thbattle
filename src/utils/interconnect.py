# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from gevent import Greenlet
import gevent
import redis
import simplejson as json

# -- own --
from .misc import surpress_and_restart
from endpoint import Endpoint


# -- code --
class Interconnect(Greenlet):
    def __init__(self, node, url):
        Greenlet.__init__(self)
        self.node = node
        self.pub = redis.from_url(url)
        self.sub = redis.from_url(url)

    @surpress_and_restart
    def _run(self):
        try:
            sub = self.sub.pubsub()
            sub.psubscribe('thb.*')

            for msg in sub.listen():
                if msg['type'] not in ('message', 'pmessage'):
                    continue

                _, node, topic = msg['channel'].split('.')[:3]
                message = json.loads(msg['data'])

                self.on_message(node, topic, message)

        finally:
            gevent.sleep(1)

    def on_message(self, node, topic, message):
        pass

    def publish(self, topic, data):
        self.pub.publish(
            'thb.{}.{}'.format(self.node, topic),
            Endpoint.encode(data, Endpoint.FMT_RAW_JSON),
        )

    def __repr__(self):
        return self.__class__.__name__
