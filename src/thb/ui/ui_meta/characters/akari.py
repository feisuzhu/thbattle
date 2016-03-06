# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(characters.akari)


class Akari:
    # Character
    char_name = u'随机角色'
    port_image = 'thb-portrait-akari'
    description = (
        u'|DB会是谁呢 随机角色 体力：?|r\n\n'
        u'|G阿卡林|r：消失在画面里的能力。在开局之前，没有人知道这是谁。'
    )
