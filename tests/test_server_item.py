# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from nose.tools import eq_, assert_raises
from game.base import GameItem
from utils import exceptions

# -- own --
from db.session import current_session, transactional
import options as opmodule

# -- code --


class options(object):
    db = 'sqlite://'
    freeplay = True

opmodule.options.__dict__.update(options.__dict__)


@GameItem.register
class Foo(GameItem):
    key, args, usable, title = 'foo', [], True, 'Foo'
    description = u'没什么用，测试用的'
    use = lambda *a: 0


@GameItem.register
class Bar(GameItem):
    key, args, usable, title = 'bar', [], False, 'Bar'
    description = u'没什么用，测试用的'


class TestExchange(object):

    @classmethod
    def setUpClass(cls):
        import db.session
        db.session.init(options.db)

    def setUp(self):
        from db.session import Session, DBState
        from db.models import User, Item, DiscuzMember, DiscuzMemberCount
        from db.base import Model
        Model.metadata.drop_all(DBState.engine)
        Model.metadata.create_all(DBState.engine)
        s = Session()
        [s.add(i) for i in [
            User(id=1, username='1', jiecao=100000, ppoint=1000, title='', email='1@test.com'),
            User(id=2, username='2', jiecao=100000, ppoint=1000, title='', email='2@test.com'),
            DiscuzMember(uid=1, username='1'),
            DiscuzMember(uid=2, username='2'),
            DiscuzMemberCount(uid=1, jiecao=100000),
            DiscuzMemberCount(uid=2, jiecao=100000),
            Item(id=1, owner_id=1, sku='foo', status='backpack'),
            Item(id=2, owner_id=2, sku='bar', status='backpack'),
        ] if not options.freeplay or 'DiscuzMember' not in i.__class__.__name__]
        s.commit()

    @transactional('new', isolation_level='READ_COMMITTED')
    def testExchange(self):
        from db.models import Exchange, User, Item
        from server.item import exchange

        s = current_session()

        s.rollback()
        exchange.sell(uid=1, item_id=1, price=500)
        eq_(s.query(Item).filter(Item.owner_id != None).count(), 1)  # noqa
        e = s.query(Exchange).first()
        eq_(e.item.sku, 'foo')
        eid = e.id

        s.rollback()
        exchange.buy(uid=2, entry_id=eid)

        u1, u2 = s.query(User).order_by(User.id.asc()).all()
        eq_(u1.ppoint, 1500)
        eq_(u2.ppoint, 500)

        i1, i2 = s.query(Item).order_by(Item.id.asc()).all()
        eq_(i1.owner_id, 2)
        eq_(i2.owner_id, 2)

        with assert_raises(exceptions.UserNotFound):
            exchange.buy(uid=3, entry_id=3)

        with assert_raises(exceptions.ItemNotFound):
            exchange.buy(uid=1, entry_id=3)

        s.rollback()
        id = s.query(Item).first().id
        exchange.sell(uid=2, item_id=id, price=5000)
        s.rollback()
        id = s.query(Exchange).first().id

        with assert_raises(exceptions.InsufficientFunds):
            exchange.buy(uid=1, entry_id=id)

        exchange.cancel_sell(uid=2, entry_id=id)

        i1, i2 = s.query(Item).order_by(Item.id.asc()).all()
        eq_(i1.owner_id, 2)
        eq_(i2.owner_id, 2)

        exchange.list()

    @transactional('new', isolation_level='READ_COMMITTED')
    def testBackpack(self):
        from db.models import User, Item, DiscuzMember
        from server.item import backpack, constants

        s = current_session()

        backpack.use(1, 'foo')

        with assert_raises(exceptions.ItemNotFound):
            backpack.use(1, 'foo')

        with assert_raises(exceptions.ItemNotFound):
            backpack.use(1, 'bar')

        backpack.add(1, 'foo')
        backpack.use(1, 'foo')

        backpack.add(1, 'bar')

        with assert_raises(exceptions.ItemNotUsable):
            backpack.use(1, 'bar')

        s.rollback()
        id = s.query(Item).filter(Item.owner_id == 1, Item.sku == 'bar').first().id
        backpack.drop(1, id)

        for i in xrange(constants.BACKPACK_SIZE):
            backpack.add(1, 'foo')

        with assert_raises(exceptions.BackpackFull):
            backpack.add(1, 'foo')

        eq_(len(backpack.list(1)), constants.BACKPACK_SIZE)

        s.rollback()
        id = s.query(Item).filter(Item.owner_id == 1).first().id

        backpack.drop(1, id)
        eq_(len(backpack.list(1)), constants.BACKPACK_SIZE - 1)

        with assert_raises(exceptions.ItemNotFound):
            backpack.drop(1, id)

        s.rollback()
        u = s.query(User).filter(User.id == 1).first()
        u.ppoint = 0
        if not options.freeplay:
            dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == 1).first()
            dz_member.member_count.jiecao = 0
        else:
            u.jiecao = 0
        s.commit()

        backpack.add(1, 'jiecao:1234')
        backpack.use(1, 'jiecao:1234')
        backpack.add(1, 'ppoint:1234')
        backpack.use(1, 'ppoint:1234')

        u = s.query(User).filter(User.id == 1).first()
        eq_(u.ppoint, 1234)
        if not options.freeplay:
            dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == 1).first()
            eq_(dz_member.member_count.jiecao, 1234)

    @transactional('new', isolation_level='READ_COMMITTED')
    def testLottery(self):
        from db.models import User, DiscuzMember
        from server.item import constants, lottery

        lottery.draw(1, 'jiecao')
        lottery.draw(1, 'ppoint')
        lottery.draw(1, 'jiecao')
        lottery.draw(1, 'ppoint')
        lottery.draw(1, 'jiecao')
        lottery.draw(1, 'ppoint')

        s = current_session()
        u = s.query(User).filter(User.id == 1).first()
        eq_(u.ppoint, 1000 - constants.LOTTERY_PRICE * 3)
        if not options.freeplay:
            dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == 1).first()
            eq_(dz_member.member_count.jiecao, 100000 - constants.LOTTERY_JIECAO_PRICE * 3)

            dz_member.member_count.jiecao = 0
        else:
            u.jiecao = 0

        s.commit()

        with assert_raises(exceptions.InsufficientFunds):
            lottery.draw(1, 'jiecao')
