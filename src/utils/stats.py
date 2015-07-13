# -*- coding: utf-8 -*-

# -- stdlib --
import json
import sys
import uuid

# -- third party --
import gevent
import requests

# -- own --
from settings import LEANCLOUD_APPID, LEANCLOUD_APPKEY, VERSION
from user_settings import UserSettings


# -- code --
SESSION = str(uuid.uuid4())


# {'event': '_page', 'duration': 2000, 'tag': 'BookDetail'},
# {'event': 'buy-item', 'attributes': {'item-category': 'book'}, 'metrics': {'amount': 9.99}},
# {'event': '_session.close', 'duration': 10000}

def _stats(events):
    if not events: return

    for i in xrange(3):
        try:
            requests.post(
                'https://api.leancloud.cn/1.1/stats/open/collect',
                headers={
                    'Content-Type': 'application/json',
                    'X-AVOSCloud-Application-Id': LEANCLOUD_APPID,
                    'X-AVOSCloud-Application-Key': LEANCLOUD_APPKEY,
                },
                data=json.dumps({
                    'client': {
                        'id': UserSettings.client_id,
                        'platform': sys.platform,
                        'app_version': VERSION,
                        'app_channel': 'thbattle.net',
                    },
                    'session': {
                        'id': SESSION,
                    },
                    'events': events,
                })
            )
            break

        except Exception:
            import traceback
            traceback.print_exc()
            gevent.sleep(1)
            continue


def stats(*events):
    gevent.spawn(_stats, events)
