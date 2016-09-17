# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- prioritized --
import sys
sys.path.append('../src')

from game import autoenv
autoenv.init('Client')

# -- stdlib --
import json
import re

# -- third party --
from unidecode import unidecode

# -- own --
from game.autoenv import Game
from thb import cards, characters
from thb.ui.ui_meta.common import metadata, char_desc


# -- code --
def to_html(text):
    result   = []
    tagstack = []

    def push(klass):
        def scanner_cb(s, tok):
            result.append('<span class="{}">'.format(klass))
            tagstack.append('span')
        return scanner_cb

    def pop(klass):
        def scanner_cb(s, tok):
            result.append('</span>')
            t = tagstack.pop()
            assert t == 'span'  # not so corrent
        return scanner_cb

    def restore(s, tok):
        for i in reversed(tagstack):
            result.append('</{}>'.format(i))

        tagstack[:] = []

    def error(s, tok):
        raise Exception('%s\n%s' % (s, tok))

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
        (r'\|B',  push('bold')),
        (r'\|b',  pop('bold')),
        (r'\|I',  push('italic')),
        (r'\|i',  pop('italic')),
        (r'\|U',  push('underline')),
        (r'\|u',  pop('underline')),
        (r'\|\|', insert_pipe),
        (r'\|r',  restore),

        # shortcuts
        (r'\|R',  push('shortcut-r')),
        (r'\|G',  push('shortcut-g')),
        (r'\|Y',  push('shortcut-y')),
        (r'\|LB', push('shortcut-lb')),
        (r'\|DB', push('shortcut-db')),
        (r'\|W',  push('shortcut-w')),

        # thbviewer labels
        (r'\|!R', label('important')),
        (r'\|!G', label('success')),
        (r'\|!O', label('warning')),
        (r'\|!B', label('info')),
    ])

    toks, reminder = scanner.scan(text)
    reminder and instext(None, reminder)

    return u''.join(result)


def conv_card_category(t):
    return tuple([_card_category[i] for i in t])


_card_category = {
    'basic':             u'基本牌',
    'spellcard':         u'符卡',
    'delayed_spellcard': u'延时符卡',
    'instant_spellcard': u'非延时符卡',
    'equipment':         u'装备',
    'weapon':            u'武器',
    'shield':            u'防具',
    'redufo':            u'红色UFO',
    'greenufo':          u'绿色UFO',
    'accessories':       u'饰品',
    'group_effect':      u'群体',
}


result = {
    'Cards':      [],
    'Characters': [],
    'Modes':      [],
}

#  --- Cards ---
excludes = [
    cards.HiddenCard,
    cards.DummyCard,
    cards.MassiveDamageCard,
]


def snstring(suit, num):
    num = ' A23456789_JQK'[num]
    if num == '_': num = '10'
    return ftstring[suit] + num

ftstring = {
    cards.Card.SPADE:   u'♠',
    cards.Card.HEART:   u'♡',
    cards.Card.CLUB:    u'♣',
    cards.Card.DIAMOND: u'♢',
}


def find_cards(cardcls):
    lst = [(n, s) for (cls, s, n) in cards.card_definition if cls is cardcls]
    lst.sort()
    return [snstring(s, n) for n, s in lst]


for k, v in metadata.iteritems():
    if not issubclass(k, cards.Card): continue
    if issubclass(k, cards.VirtualCard): continue
    if k in excludes: continue
    result['Cards'].append({
        "token":         k.__name__,
        "image":         "{}.png".format(v['image'].replace('-', '/')),
        "name":          v['name'],
        "categories":    conv_card_category(k.category),
        "description":   to_html(v['description']),
        "fulltextindex": unidecode(v['description']).replace(' ', '').lower(),
        "deck":          find_cards(k),
    })


#  --- Characters ---
excludes = [
    characters.akari.Akari,
]

for k, v in metadata.iteritems():
    if not issubclass(k, characters.baseclasses.Character): continue
    if k in excludes: continue
    if not getattr(k, 'categories', False): continue
    desc = char_desc(k)
    result['Characters'].append({
        "token":         k.__name__,
        "image":         "{}.png".format(v['port_image'].replace('-', '/')),
        "name":          v['name'],
        "maxlife":       k.maxlife,
        "modes":         k.categories,
        "description":   to_html(desc),
        "fulltextindex": unidecode(desc).replace(' ', '').lower(),
        "positions":     ("暂缺",),
    })


#  --- Modes ---
for k, v in metadata.iteritems():
    if not issubclass(k, Game): continue
    result['Modes'].append({
        "token":       k.__name__,
        "image":       "{}.png".format(v['logo'].replace('-', '/')),
        "name":        v['name'],
        "description": to_html(v.get('description', u'暂缺')),
    })


#  --- Save result ---
with open('/dev/shm/thbviewer.json', 'w') as f:
    f.write(json.dumps(result))
