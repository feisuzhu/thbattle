# -*- coding: utf-8 -*-
# -- stdlib --
import sys
import argparse
from urllib import unquote
import atexit

# -- third party --
import gevent
from gevent import monkey
monkey.patch_all()

from gevent.event import AsyncResult
from gevent import Timeout, Greenlet
from bottle import route, run, request, response
import pika
import simplejson as json

# -- own --
from utils import instantiate, swallow, surpress_and_restart
from utils.rpc import RPCClient
from network import Endpoint


# -- code --
parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=7001)
parser.add_argument('--discuz-cookiepre', default='VfKd_')
options = parser.parse_args()


member_service = RPCClient(('127.0.0.1', 7000), timeout=2)
event_waiters = set()

@instantiate
class Interconnect(object):
    def __init__(self):
        self.conn = conn = pika.BlockingConnection()
        self.chan = chan = conn.channel()
        chan.exchange_declare('thb_events', 'fanout')

    def publish(self, key, body):
        self.chan.basic_publish(
            'thb_events', '%s:%s' % ('forum', key),
            Endpoint.encode(body),
        )

    def shutdown(self):
        swallow(self.chan.close)()
        swallow(self.conn.close)()

atexit.register(Interconnect.shutdown)


class InterconnectHandler(Greenlet):
    @surpress_and_restart
    def _run(self):
        try:
            conn = pika.BlockingConnection()
            chan = conn.channel()
            chan.exchange_declare('thb_events', 'fanout')
            queue = chan.queue_declare(
                exclusive=True,
                auto_delete=True,
                arguments={'x-message-ttl': 1000},
            )
            chan.queue_bind(queue.method.queue, 'thb_events')

            for method, header, body in chan.consume(queue.method.queue):
                chan.basic_ack(method.delivery_tag)
                message = json.loads(body)
                key = method.routing_key
                node, topic = key.split(':')

                if topic in ('speaker', 'current_users'):
                    @gevent.spawn
                    def notify(message=message, node=node):
                        encoded = json.dumps([key, message])
                        for a in list(event_waiters):
                            a.set(encoded)

        finally:
            swallow(chan.close)()
            swallow(conn.close)()
            gevent.sleep(1)

    def __repr__(self):
        return self.__class__.__name__

InterconnectHandler = InterconnectHandler.spawn()


@route('/events')
def events():
    try:
        waiter = AsyncResult()
        event_waiters.add(waiter)
        return waiter.get(timeout=30)

    except Timeout:
        return 'null'

    finally:
        event_waiters.discard(waiter)


@route('/speaker')
def speaker():
    if request.method != 'POST':
        response.status = 405
        return

    idx = {
        k.split('_')[-1]: k for k in request.cookies
        if k.startswith(options.discuz_cookiepre)
    }

    if not ('auth' in idx and 'saltkey' in idx):
        response.status = 403
        return

    auth = unquote(request.get_cookie(idx['auth']))
    saltkey = unquote(request.get_cookie(idx['saltkey']))
    member = member_service.validate_by_cookie(auth, saltkey)

    if member['credits'] < 10:
        return 'false'

    message = request.params.get('message').decode('utf-8', 'ignore')
    username = member['username'].decode('utf-8', 'ignore')
    member_service.add_credit(member['uid'], 'credits', -10)

    Interconnect.publish('speaker', [username, message])

    return 'true'


run(server='gevent', host=options.host, port=options.port)
