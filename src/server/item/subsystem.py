# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --

# -- own --
from server.item import backpack, exchange, lottery
from utils import BusinessException


# -- code --
log = logging.getLogger('ItemSystem')


class ItemSystem(object):

    def __init__(self):
        self.command_dispatch = {
            'backpack':    self.list_backpack,
            'use':         self.do_use,
            'drop':        self.do_drop,
            'exchange':    self.list_exchange,
            'buy':         self.do_buy,
            'sell':        self.do_sell,
            'cancel_sell': self.do_cancel_sell,
            'lottery':     self.do_lottery,
        }

    def _command(*argstype):
        def decorate(f):
            f._contract = argstype
            return f

        return decorate

    def process_command(self, user, cmd, args):
        dispatch = self.command_dispatch
        handler = dispatch.get(cmd)

        if not user.account:
            user.write(['error', 'not_logged_in'])
            return

        if not handler:
            log.info('Unknown command %s', cmd)
            user.write(['invalid_item_command', [cmd, args]])
            return

        argstype = handler._contract

        if not (len(argstype) == len(args) and all(isinstance(v, t) for t, v in zip(argstype, args))):
            log.debug('Command %s with wrong args, expecting %r, actual %r', cmd, argstype, args)
            user.write(['invalid_item_command', [cmd, args]])
            return

        try:
            handler(user, *args)
        except BusinessException as e:
            user.write(['error', e.snake_case])

    @_command()
    def list_backpack(self, user):
        user.write(['items', backpack.list(user.userid)])

    @_command(int)
    def do_use(self, user, item_):
        backpack.use(user.userid, item_)
        user.write(['message', 'success'])

    @_command(int)
    def do_drop(self, user, item_id):
        backpack.drop(user.userid, item_id)
        user.write(['message', 'success'])

    @_command()
    def list_exchange(self, user):
        l = exchange.list()
        user.write(['exchange', l])

    @_command(int, int)
    def do_sell(self, user, item_id, price):
        exchange.sell(user.userid, id)
        user.write(['message', 'success'])

    @_command(int)
    def do_buy(self, user, entry_id):
        exchange.buy(user.userid, entry_id)
        user.write(['message', 'success'])

    @_command(int)
    def do_cancel_sell(self, user, entry_id):
        exchange.cancel_sell(user.userid, entry_id)
        user.write(['message', 'success'])

    @_command(basestring)
    def do_lottery(self, user, currency):
        reward = lottery.draw(user, currency)
        user.write(['lottery_reward', reward])
