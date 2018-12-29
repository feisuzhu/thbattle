# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging
import sys

# -- third party --

# -- own --
from server.item import backpack, exchange, lottery
from utils import BusinessException


# -- code --
log = logging.getLogger('ItemSystem')


class ItemSystem(object):

    def __init__(self):
        self.command_dispatch = {
            'backpack':    self.backpack,
            'use':         self.use,
            'drop':        self.drop,
            'exchange':    self.exchange,
            'buy':         self.buy,
            'sell':        self.sell,
            'cancel_sell': self.cancel_sell,
            'lottery':     self.lottery,
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
            user.write(['message_err', 'not_logged_in'])
            return

        if not handler:
            log.info('Unknown item command %s', cmd)
            return

        argstype = handler._contract

        if not (len(argstype) == len(args) and all(isinstance(v, t) for t, v in zip(argstype, args))):
            log.debug('Command %s with wrong args, expecting %r, actual %r', cmd, argstype, args)
            return

        try:
            handler(user, *args)
        except BusinessException as e:
            log.info("Command %s execution failed, user: %s, args: %s",
                     user.account.userid, args,
                     exc_info=sys.exc_info())
            user.write(['message_err', e.snake_case])

    @_command()
    def backpack(self, user):
        user.write(['backpack', backpack.list(user.account.userid)])

    @_command(int)
    def use(self, user, item_):
        backpack.use(user.account.userid, item_)
        user.write(['message_info', 'success'])

    @_command(int)
    def drop(self, user, item_id):
        backpack.drop(user.account.userid, item_id)
        user.write(['message_info', 'success'])

    @_command()
    def exchange(self, user):
        l = exchange.list()
        user.write(['exchange', l])

    @_command(int, int)
    def sell(self, user, item_id, price):
        exchange.sell(user.account.userid, id)
        user.write(['message_info', 'success'])

    @_command(int)
    def buy(self, user, entry_id):
        exchange.buy(user.account.userid, entry_id)
        user.write(['message_info', 'success'])

    @_command(int)
    def cancel_sell(self, user, entry_id):
        exchange.cancel_sell(user.account.userid, entry_id)
        user.write(['message_info', 'success'])

    @_command(basestring)
    def lottery(self, user, currency):
        reward = lottery.draw(user.account.userid, currency)
        user.write(['lottery_reward', reward])
