# -*- coding: utf-8 -*-

# update-url: points to git repo
# server has version, and a branch name(eg 'production', 'testing').
# client always tracks corresponding branch.
#
# replay: saves current commit sha1 as version.
# when playing, switch to that version.

# -- stdlib --
from threading import RLock
import logging

# -- third party --
from gevent.hub import get_hub
import gevent
import pygit2

# -- own --

# -- code --
log = logging.getLogger('autoupdate')


class Autoupdate(object):
    def __init__(self, base):
        self.base = base

    def update(self):
        repo = pygit2.Repository(self.base)
        hub = get_hub()
        noti = hub.loop.async()
        lock = RLock()
        stats = []

        def progress(s):
            with lock:
                stats.append(s)
                noti.send()

        remote = repo.remotes[0]
        remote.transfer_progress = progress

        def do_fetch():
            try:
                return remote.fetch()
            except Exception as e:
                return e

        fetch = hub.threadpool.spawn(do_fetch)

        while True:
            noti_w = gevent.spawn(lambda: hub.wait(noti))
            for r in gevent.iwait([noti_w, fetch]):
                break

            noti_w.kill()

            if r is fetch:
                rst = r.get()
                if isinstance(rst, Exception):
                    raise rst
                else:
                    return

            v = None
            with lock:
                if stats:
                    v = stats[-1]

                stats[:] = []

            if v:
                yield v

    def switch(self, version):
        repo = pygit2.Repository(self.base)
        try:
            desired = repo.revparse_single(version)
        except KeyError:
            return False

        repo.reset(desired.id, pygit2.GIT_RESET_HARD)
        return True

    def is_version_match(self, version):
        repo = pygit2.Repository(self.base)
        try:
            current = repo.revparse_single('HEAD')
            desired = repo.revparse_single(version)
            return current.id == desired.id
        except KeyError:
            return False
