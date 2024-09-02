# -*- coding: utf-8 -*-

# -- prioritized --
import sys
sys.path.append('../src')

# -- stdlib --
from urlparse import urljoin
import argparse
import gzip
import json

# -- third party --
# -- own --
from client.core.replay import Replay
from game import autoenv
from settings import ACCOUNT_FORUMURL


# -- code --
def gen_fake_account(name, is_freeplay):
    if is_freeplay:
        acc = ['freeplay', 1, name]
    else:
        acc = ['forum', 1, name, {
            'title': u'转换的Replay只有名字啊……',
            'avatar': urljoin(ACCOUNT_FORUMURL, '/maoyu.png'),
            'credits': 1000,
            'games': 0,
            'drops': 0,
            'badges': [],
        }]

    return {'account': acc, 'state': 'ingame'}


def main():
    autoenv.init('Client')

    parser = argparse.ArgumentParser('log2thbrep')
    parser.add_argument('replay_file', help='Server side replay')
    parser.add_argument('client_version', help='Desired client version (git commit)')
    parser.add_argument('--freeplay', action='store_true', help='Use freeplay account module?')
    options = parser.parse_args()

    if options.replay_file.endswith('.gz'):
        data = gzip.open(options.replay_file, 'r').read()
    else:
        data = open(options.replay_file, 'r').read()

    data = data.decode('utf-8').split('\n')
    names = data.pop(0)[2:].split(', ')  # Names
    data.pop(0)  # Ver
    gid = int(data.pop(0).split()[-1])  # GameId
    data.pop(0)  # Time

    game_mode, game_params, game_items, rnd_seed, usergdhist, gdhist = data
    gdhist = json.loads(gdhist)
    game_params = json.loads(game_params)

    rep = Replay()
    rep.client_version = options.client_version
    rep.game_mode = game_mode
    rep.game_params = game_params
    rep.game_items = json.loads(game_items)
    rep.users = [gen_fake_account(i, options.freeplay) for i in names]

    assert len(names) == len(gdhist), [names, len(gdhist)]

    for i, gd in enumerate(gdhist):
        fn = '%s_%s.thbrep' % (gid, i)
        with open(fn, 'wb') as f:
            print 'Writing %s...' % fn
            rep.me_index = i
            rep.gamedata = gd
            f.write(rep.dumps())


if __name__ == '__main__':
    main()
