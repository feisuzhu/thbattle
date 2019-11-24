# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --

# -- code --
# {'event': '_page', 'duration': 2000, 'tag': 'BookDetail'},
# {'event': 'buy-item', 'attributes': {'item-category': 'book'}, 'metrics': {'amount': 9.99}},
# {'event': '_session.close', 'duration': 10000}


def stats(*events):
    # disable
    return
    # gevent.spawn(_stats, events)
