#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os


def _set_bootstrap_path():
    A, D, J = os.path.abspath, os.path.dirname, os.path.join
    res_path = J(D(D(A(__file__))), 'Resources')

    sys.path[0:0] = [J(res_path, i) for i in (
        'pygit2.egg', 'cffi.egg', 'pycparser.egg'
    )]

    return res_path


def set_path():
    _set_bootstrap_path()

    for i in xrange(2):
        try:
            workdir = os.path.expanduser("~/.thbattle")

            os.chdir(workdir)

            sys.path[0:0] = [
                os.path.join('./osx-eggs', i)
                for i in os.listdir('./osx-eggs')
                if i.endswith('.egg')
            ]

            sys.path[0:0] = ["./src"]

            os.environ['LD_LIBRARY_PATH'] = os.path.join(workdir, 'osx-eggs')

        except Exception:
            import traceback
            traceback.print_exc()
            populate_dot_thbattle()
            continue

        break


def populate_dot_thbattle():
    res_path = _set_bootstrap_path()

    os.system('rm -rf ~/.thbattle/{osx-eggs,src}')
    os.system('mkdir -p ~/.thbattle/osx-eggs && cd ~/.thbattle/osx-eggs && tar -xf %s' % os.path.join(res_path, 'osx-eggs.tar'))
    os.system('mkdir -p ~/.thbattle/src && cd ~/.thbattle/src && tar -xf %s' % os.path.join(res_path, 'src.tar'))

    import pygit2

    repo = pygit2.Repository(os.path.expanduser("~/.thbattle/osx-eggs"))
    repo.reset(repo.revparse_single("origin/master").id, pygit2.GIT_RESET_HARD)

    repo = pygit2.Repository(os.path.expanduser("~/.thbattle/src"))
    repo.reset(repo.revparse_single("origin/production").id, pygit2.GIT_RESET_HARD)


if __name__ == '__main__':
    set_path()

    import start_client
    sys.exit(start_client.start_client())
