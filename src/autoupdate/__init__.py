import gevent
import gevent.httplib
import gevent.queue
import urllib2
from hashlib import sha1
import simplejson as json
import os
from urlparse import urljoin

import logging
log = logging.getLogger('autoupdate')

import re

ignores = re.compile(r'''
          ^current_version$
        | ^update_info\.json$
        | ^.+\.py[co]$
        | ^.*~$
        | ^\.
''', re.VERBOSE)

def build_hash(base):
    my_hash = {}
    for path, _, names in os.walk(base):
        # exclude list
        for name in names:
            if ignores.match(name):
                continue
            fn = os.path.join(path, name)
            with open(fn, 'rb') as f:
                h = sha1(f.read()).hexdigest()
                my_hash[h] = fn
    return my_hash

def version_string(hash):
    return sha1(''.join(sorted(hash.keys()))).hexdigest()

def write_metadata(base):
    h = build_hash(base)
    with open('update_info.json', 'w') as f:
        f.write(json.dumps(h))

    with open('current_version', 'w') as f:
        f.write(version_string(h))

def do_update(base, url, cb=lambda *a, **k: False):

    try:
        remote = urllib2.build_opener()
        cb('update_begin')

        def worker(url):
            resp = remote.open(url)
            rst = resp.read()
            resp.close()
            return rst

        latest_ver = gevent.spawn(worker, urljoin(url, 'current_version'))

        my_hash = build_hash(base)
        my_ver = version_string(my_hash)

        latest_ver = latest_ver.get().strip()

        if my_ver == latest_ver:
            log.info('game up to date')
            cb('update_up2date')
            return 'up2date'

        latest_hash = json.loads(worker(urljoin(url, 'update_info.json')))

        my_set = set(my_hash.keys())
        latest_set = set(latest_hash.keys())
        files_delete = my_set - latest_set
        files_update = latest_set - my_set


        for h in files_delete:
            fn = my_hash[h]
            fn = os.path.relpath(fn)
            cb('delete_file', fn)
            log.info('delete file %s', fn)
            try: os.unlink(fn)
            except OSError: pass

        queue = gevent.queue.Queue(100)
        for h in files_update:
            fn = latest_hash[h]
            suburl = os.path.relpath(fn, base).replace('\\', '/')
            queue.put(
                (urljoin(url, suburl), fn)
            )

        def retrieve_worker():
            try:
                while True:
                    url, fn = queue.get_nowait()
                    cb('download_file', fn)
                    file = remote.open(url)
                    d = file.read()
                    file.close()
                    try:
                        try:
                            os.makedirs(os.path.dirname(fn))
                        except OSError:
                            pass

                        with open(fn, 'wb') as f:
                            f.write(d)
                    except EnvironmentError:
                        cb('write_failed', fn)
            except gevent.queue.Empty:
                pass

        workers = [gevent.spawn(retrieve_worker) for i in range(3)]
        for w in workers: w.join()

        cb('update_finished')

        return 'updated'

    except urllib2.HTTPError as e:
        cb('http_error', e.getcode(), e.geturl())

    except urllib2.URLError as e:
        cb('network_error')

    except IOError as e:
        cb('io_error')

    return 'error'

# autoupdate.do_update('.', 'http://127.0.0.1/src/')
