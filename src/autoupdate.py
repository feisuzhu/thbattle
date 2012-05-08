import gevent
import gevent.queue
import urllib2
from zlib import crc32
import simplejson as json
import os
from urlparse import urljoin

import logging
log = logging.getLogger('autoupdate')

import re

ignores = re.compile(r'''
          ^current_version$
        | ^update_info\.json$
        | ^client_log\.txt$
        | ^.+\.py[co]$
        | ^.*~$
        | ^\.
''', re.VERBOSE)

def build_hash(base):
    my_hash = {}
    cwd = os.getcwd()
    for path, _, names in os.walk(base):
        # exclude list
        for name in names:
            if ignores.match(name):
                continue
            fn = os.path.join(path, name)
            fn = os.path.relpath(fn, cwd)
            with open(fn, 'rb') as f:
                h = crc32(f.read())
                my_hash[fn.replace('\\', '/')] = h
    return my_hash

def version_string(hash):
    return str(crc32(str(sorted(hash.values()))))

def write_metadata(base):
    h = build_hash(base)
    with open('update_info.json', 'w') as f:
        f.write(json.dumps(h, indent='    '))

    with open('current_version', 'w') as f:
        f.write(version_string(h))

def do_update(base, update_url, cb=lambda *a, **k: False):

    try:
        remote = urllib2.build_opener()
        cb('update_begin')

        me = gevent.getcurrent()

        def worker(url):
            try:
                resp = remote.open(url)
                rst = resp.read()
                resp.close()
                return rst
            except Exception as e:
                me.kill(e)

        latest_ver = gevent.spawn(worker, urljoin(update_url, 'current_version'))

        write_metadata(base)
        my_hash = build_hash(base)
        my_ver = version_string(my_hash)

        latest_ver = latest_ver.get().strip()

        if my_ver == latest_ver:
            log.info('game up to date')
            cb('up2date')
            return 'up2date'

        latest_hash = json.loads(worker(urljoin(update_url, 'update_info.json')))

        my_set = set(my_hash.items())
        latest_set = set(latest_hash.items())
        files_delete = my_set - latest_set
        files_update = latest_set - my_set

        ''' # Temp disabled
        for fn, _ in files_delete:
            fn = os.path.relpath(fn)
            cb('delete_file', fn)
            log.info('delete file %s', fn)
            try: os.unlink(fn)
            except OSError: pass
        '''

        queue = gevent.queue.Queue(1000000)
        for fn, _ in files_update:
            suburl = os.path.relpath(fn, base).replace('\\', '/')
            print update_url, suburl, urljoin(update_url, suburl)
            queue.put(
                (urljoin(update_url, suburl), fn)
            )

        def retrieve_worker():
            try:
                while True:
                    url, fn = queue.get_nowait()
                    log.debug('update %s' % fn)
                    cb('download_file', fn)
                    file = remote.open(url)
                    d = file.read()
                    file.close()
                    cb('download_complete', fn)
                    try:
                        try:
                            os.makedirs(os.path.dirname(fn))
                        except OSError:
                            pass
                        #with open(fn, 'wb') as f:
                        #    f.write(d)
                    except EnvironmentError:
                        cb('write_failed', fn)
            except gevent.queue.Empty:
                pass

            except Exception as e:
                me.kill(e)

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
