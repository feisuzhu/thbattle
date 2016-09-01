# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import os
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# -- third party --
# -- own --

# -- code --


def p(k):
    global cls
    return cls.pop(k)


def __metaclass__(clsname, bases, _dict):
    global cls
    cls = _dict
    p('__module__')
    cls['__name__'] = clsname
    return cls


'''
class Aya:
    # Character
    char_name = u'射命丸文'
    port_image = 'thb-portrait-aya'
    figure_image = 'thb-figure-aya'
    miss_sound_effect = 'thb-cv-aya_miss'
    description = (
        u'|DB幻想乡最速 射命丸文 体力：4|r\n\n'
        u'|G最速|r：|B锁定技|r，你在回合内使用第二张牌时，你摸一张牌且在本回合使用卡牌时无距离限制。\n\n'
        u'|DB（画师：渚FUN，CV：君寻）|r'
    )
'''

exec sys.stdin.read().decode('utf-8').strip()

lines = cls.pop('description').split(u'\n\n')
header, skills, credit = lines[0], lines[1:-1], lines[-1]

title, fullname, _ = header.replace(u'|DB', u'').replace(u'|r', u'').split()

print u'''
class {cls}:
    # Character
    name        = u'{name}'
    fullname    = u'{fullname}'
    title       = u'{title}'
'''.strip().format(cls=cls.pop('__name__'), name=cls.pop('char_name'), fullname=fullname, title=title)


mapping = {
    u'画师': u'illustrator',
    u'CV': u'cv',
    u'人物设计': u'designer',
}

credit = credit.replace(u'|DB', u'').replace(u'|r', u'')
pairs = re.findall(ur'（?(.*?)：(.*?)(，|）)', credit)

n = max(map(len, mapping.values()))
for k, v, _ in pairs:
    print u"    %s = u'%s'" % ((mapping.get(k, k) + u' ' * n)[:n], v)


print u'''
    port_image        = u'{port}'
    figure_image      = u'{figure}'
    miss_sound_effect = u'{miss}'
'''.format(port=cls.pop('port_image'), figure=cls.pop('figure_image', ''), miss=cls.pop('miss_sound_effect', ''))

for s in skills:
    if u'：' not in s:
        assert s == skills[-1]
        print u"    notes = u'%s'" % s
        break
    n, d = s.split(u'：', 1)
    print u'    # %s' % n
    print u"    description = u'%s'" % d

assert cls == {}, cls
