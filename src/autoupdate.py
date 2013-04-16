import gevent
import gevent.queue
import urllib2
from zlib import crc32
import simplejson as json
import sys, os
from urlparse import urljoin
from StringIO import StringIO
from gzip import GzipFile

import logging
log = logging.getLogger('autoupdate')

import settings

ignores = settings.UPDATE_IGNORES
VERSION = settings.VERSION

def build_hash(base):
    my_hash = {}
    for path, _, names in os.walk(base):
        for name in names:
            if ignores.match(name):
                # file in exclude list
                continue
            fn = os.path.join(path, name)
            rfn = os.path.relpath(fn, base)
            with open(fn, 'rb') as f:
                h = crc32(f.read())
                my_hash[rfn.replace('\\', '/')] = h
    return my_hash

def version_string(hash):
    return str(crc32(str(sorted(hash.values()))))

def write_metadata(base):
    h = build_hash(base)
    with open('update_info.json', 'w') as f:
        f.write(json.dumps(h, encoding=sys.getfilesystemencoding(), indent='    '))

    with open('current_version', 'w') as f:
        f.write(version_string(h))

def do_update(base, update_url, cb=lambda *a, **k: False):

    try:
        remote = urllib2.build_opener()
        remote.addheaders = [('User-Agent', VERSION), ('Accept-Encoding', 'gzip')]
        cb('update_begin')

        me = gevent.getcurrent()

        def worker(url):
            try:
                resp = remote.open(url)
                rst = resp.read()
                if resp.headers.get('Content-Encoding') == 'gzip':
                    rst = GzipFile(fileobj=StringIO(rst), mode='rb').read()
                resp.close()
                return rst
            except Exception as e:
                me.kill(e)

        latest_ver = gevent.spawn(worker, urljoin(update_url, 'current_version'))

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
        files_delete -= files_update

        for fn, _ in files_delete:
            ffn = os.path.join(base, fn)
            cb('delete_file', fn)
            log.info('delete file %s', fn)
            try: os.unlink(ffn)
            except OSError: pass

        queue = gevent.queue.Queue(1000000)
        for fn, _ in files_update:
            suburl = fn.replace('\\', '/')
            queue.put(
                (urljoin(update_url, suburl), fn)
            )

        def retrieve_worker():
            try:
                while True:
                    url, fn = queue.get_nowait()
                    log.info('update %s' % fn)
                    cb('download_file', fn)
                    resp = remote.open(url)
                    d = resp.read()
                    if resp.headers.get('Content-Encoding') == 'gzip':
                        d = GzipFile(fileobj=StringIO(d), mode='rb').read()

                    resp.close()
                    cb('download_complete', fn)
                    ffn = os.path.join(base, fn)
                    try:
                        try:
                            os.makedirs(os.path.dirname(ffn))
                        except OSError:
                            pass
                        with open(ffn, 'wb') as f:
                            f.write(d)
                    except EnvironmentError:
                        cb('write_failed', fn)
            except gevent.queue.Empty:
                pass

            except Exception as e:
                me.kill(e)

        workers = [gevent.spawn(retrieve_worker) for i in range(4)]
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
