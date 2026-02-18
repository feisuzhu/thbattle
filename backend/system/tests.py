# -*- coding: utf-8 -*-

# -- stdlib --
import datetime

# -- third party --
import factory
import pytest
import pytz

# -- own --
from . import models


# -- code --
class SMSVerificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SMSVerification

    phone = factory.Faker("phone_number")
    key   = factory.Faker("md5")
    time  = factory.LazyAttribute(lambda o: datetime.datetime.now(pytz.utc))
    used  = False


class ServerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Server

    name    = factory.Sequence(lambda n: f'server-{n}')
    version = 1
    url     = 'tcp://localhost:9999'
    branch  = 'production'
    chat    = 'ws://localhost:8888'


class SettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Setting

    key   = factory.Sequence(lambda n: f'key-{n}')
    value = 'some-value'


class NewsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.News

    text = factory.Faker('paragraph')


@pytest.mark.django_db
class TestSMSVerification:
    def test_is_verified_with_phone(self):
        v = SMSVerificationFactory.create(phone='13800138000')
        assert v.is_verified()

    def test_is_verified_without_phone(self):
        v = SMSVerificationFactory.create(phone=None)
        assert not v.is_verified()

    def test_not_expired(self):
        v = SMSVerificationFactory.create()
        assert not v.expired()

    def test_expired(self):
        v = SMSVerificationFactory.create()
        models.SMSVerification.objects.filter(pk=v.pk).update(
            time=datetime.datetime.now(pytz.utc) - datetime.timedelta(hours=2)
        )
        v.refresh_from_db()
        assert v.expired()

    def test_can_use(self):
        v = SMSVerificationFactory.create(phone='13800138000', used=False)
        assert v.can_use()

    def test_cannot_use_when_used(self):
        v = SMSVerificationFactory.create(phone='13800138000', used=True)
        assert not v.can_use()

    def test_cannot_use_when_expired(self):
        v = SMSVerificationFactory.create(phone='13800138000')
        models.SMSVerification.objects.filter(pk=v.pk).update(
            time=datetime.datetime.now(pytz.utc) - datetime.timedelta(hours=2)
        )
        v.refresh_from_db()
        assert not v.can_use()

    def test_cannot_use_without_phone(self):
        v = SMSVerificationFactory.create(phone=None)
        assert not v.can_use()


@pytest.mark.django_db
def test_servers_query(Q):
    ServerFactory.create(name='cn-1')
    ServerFactory.create(name='cn-2')

    rst = Q('''
        query {
            servers { id name url }
        }
    ''')

    assert 'errors' not in rst
    assert len(rst['data']['servers']) == 2
    names = {s['name'] for s in rst['data']['servers']}
    assert names == {'cn-1', 'cn-2'}


@pytest.mark.django_db
def test_setting_query(Q):
    SettingFactory.create(key='test-key', value='test-value')

    rst = Q('''
        query {
            setting(key: "test-key")
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['setting'] == 'test-value'


@pytest.mark.django_db
def test_news_query(Q):
    NewsFactory.create(text='old news')
    NewsFactory.create(text='latest news')

    rst = Q('''
        query {
            news
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['news'] == 'latest news'


@pytest.mark.django_db
def test_news_query_empty(Q):
    rst = Q('''
        query {
            news
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['news'] == ''
