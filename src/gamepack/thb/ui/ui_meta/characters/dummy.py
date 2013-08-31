# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.dummy)


class Dummy:
    # Character
    char_name = u'机器人'
    port_image = gres.dummy_port
    description = (
        u'|DB河童工厂的残次品 机器人 体力：5|r\n\n'
        u'|G我很强壮|r：嗯，很强壮……'
    )
