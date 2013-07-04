# -*- coding: utf-8 -*-

import sys
sys.path.append('../src')

import re
import pyglet
pyglet.options['shadow_window'] = False

import simplejson as json
from game import autoenv

autoenv.init('Client')

sys.modules['gamepack.thb.ui.resource'] = sys.modules['__main__']  # dark art


class attrname(object):
    def __getattr__(self, name):
        return name


resource = attrname()


from gamepack.thb.ui.ui_meta import metadata
from gamepack.thb import cards
from gamepack.thb import characters
from game.autoenv import Game


def to_html(text):
    result = []
    tagstack = []

    def push(klass):
        def scanner_cb(s, tok):
            result.append('<span class="{}">'.format(klass))
            tagstack.append('span')
        return scanner_cb

    def restore(s, tok):
        for i in reversed(tagstack):
            result.append('</{}>'.format(i))

        tagstack[:] = []

    def error(s, tok):
        raise Exception('....')

    def instext(s, tok):
        result.append(tok.replace('\n', '<br />'))

    def color(s, tok):
        c = tok[2:8]
        result.append('<span style="color: #{};">'.format(c))
        tagstack.append('span')

    def insert_pipe(s, tok):
        instext(s, '|')

    def label(ltype):
        def scanner_cb(s, tok):
            result.append('<span class="label label-{}">'.format(ltype))
            tagstack.append('span')

        return scanner_cb

    scanner = re.Scanner([
        (r'[^|]+', instext),
        (r'\|c[A-Fa-f0-9]{8}', color),
        (r'\|B', push('bold')),
        (r'\|b', error),
        (r'\|I', push('italic')),
        (r'\|i', error),
        (r'\|U', push('underline')),
        (r'\|u', error),
        (r'\|\|', insert_pipe),
        (r'\|r', restore),

        # shortcuts
        (r'\|R', push('shortcut-r')),
        (r'\|G', push('shortcut-g')),
        (r'\|Y', push('shortcut-y')),
        (r'\|LB', push('shortcut-lb')),
        (r'\|DB', push('shortcut-db')),
        (r'\|W', push('shortcut-w')),

        # thbviewer labels
        (r'\|!R', label('important')),
        (r'\|!G', label('success')),
        (r'\|!O', label('warning')),
        (r'\|!B', label('info')),
    ])

    toks, reminder = scanner.scan(text)
    if reminder:
        instext(None, reminder)

    return u''.join(result)


def conv_card_category(t):
    return tuple([_card_category[i] for i in t])

_card_category = {
    'basic': u'基本牌',
    'spellcard': u'符卡',
    'delayed_spellcard': u'延时符卡',
    'instant_spellcard': u'立即符卡',
    'equipment': u'装备',
    'weapon': u'武器',
    'shield': u'防具',
    'redufo': u'红色UFO',
    'greenufo': u'绿色UFO',
    'accessories': u'饰品',
}


result = {
    'Cards': [],
    'Characters': [],
    'Modes': [],
}

#  --- Cards ---
excludes = [
    cards.HiddenCard,
    cards.DummyCard,
]

for k, v in metadata.iteritems():
    if not issubclass(k, cards.Card): continue
    if issubclass(k, cards.VirtualCard): continue
    if k in excludes: continue
    result['Cards'].append({
        "token": k.__name__,
        "image": "{}.png".format(v['image']),
        "name": v['name'],
        "categories": conv_card_category(k.category),
        "description": to_html(v['description']),
    })


#  --- Characters ---
excludes = [
    characters.dummy.Dummy,
    characters.remilia_ex.RemiliaEx2,
    characters.akari.Akari,
]

for k, v in metadata.iteritems():
    if not issubclass(k, characters.baseclasses.Character): continue
    if k in excludes: continue
    result['Characters'].append({
        "token": k.__name__,
        "image": "{}.png".format(v['port_image']),
        "name": v['char_name'],
        "maxlife": k.maxlife,
        "description": to_html(v['description']),
        "positions": ("暂缺",),
    })


#  --- Modes ---
for k, v in metadata.iteritems():
    if not issubclass(k, Game): continue
    result['Modes'].append({
        "token": k.__name__,
        "image": "{}.png".format(v['logo']),
        "name": v['name'],
        "description": to_html(v.get('description', u'暂缺')),
    })


#  --- Save result ---
with open('/dev/shm/thbviewer.json', 'w') as f:
    f.write(json.dumps(result))
