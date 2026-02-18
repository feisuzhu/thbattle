# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory
import pytest

# -- own --
from . import models
from authext.tests import UserFactory


# -- code --
class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Player

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('name')


@pytest.mark.django_db
def test_player_query(Q, auth_header):
    p = PlayerFactory.create(name='TestPlayer')

    rst = Q('''
        query TestPlayer($id: Int) {
            player(id: $id) { id name }
        }
    ''', variables={'id': p.id}, headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['player']['name'] == 'TestPlayer'


@pytest.mark.django_db
def test_player_query_by_name(Q, auth_header):
    PlayerFactory.create(name='UniqueNameXYZ')

    rst = Q('''
        query {
            player(name: "UniqueNameXYZ") { name }
        }
    ''', headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['player']['name'] == 'UniqueNameXYZ'


@pytest.mark.django_db
def test_player_query_not_found(Q, auth_header):
    PlayerFactory.create()

    rst = Q('''
        query {
            player(id: 99999) { name }
        }
    ''', headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['player'] is None


@pytest.mark.django_db
def test_availability_phone(Q):
    rst = Q('''
        query {
            availability { phone(phone: "13800138000") }
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['availability']['phone'] is True


@pytest.mark.django_db
def test_availability_name(Q):
    rst = Q('''
        query {
            availability { name(name: "FreshName") }
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['availability']['name'] is True


@pytest.mark.django_db
def test_availability_name_taken(Q):
    PlayerFactory.create(name='TakenName')

    rst = Q('''
        query {
            availability { name(name: "TakenName") }
        }
    ''')

    assert 'errors' not in rst
    assert rst['data']['availability']['name'] is False


@pytest.mark.django_db
def test_is_phone_number():
    assert models.is_phone_number('13800138000')
    assert not models.is_phone_number('1380013')
    assert not models.is_phone_number('17000000000')
    assert not models.is_phone_number('17100000000')
    assert not models.is_phone_number(12345678901)
    assert not models.is_phone_number('')


@pytest.mark.django_db
def test_is_name():
    assert models.is_name('GoodName')
    assert models.is_name('好名字啊')
    assert not models.is_name('ab')
    assert not models.is_name('a' * 16)
    assert not models.is_name('bad name')
    assert not models.is_name('bad%name')
    assert not models.is_name('bad*name')
