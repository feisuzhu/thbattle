# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory
import pytest

# -- own --
from . import models


# -- code --
class UnlockedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Unlocked

    player = factory.SubFactory('player.tests.PlayerFactory')
    item   = factory.Sequence(lambda n: f'char-{n}')


@pytest.mark.django_db
def test_unlock_creation():
    u = UnlockedFactory.create(item='reimu-skin-alt')
    assert u.item == 'reimu-skin-alt'
    assert u.unlocked_at is not None


@pytest.mark.django_db
def test_unlock_unique_constraint():
    from player.tests import PlayerFactory
    p = PlayerFactory.create()
    UnlockedFactory.create(player=p, item='same-item')

    with pytest.raises(Exception):
        UnlockedFactory.create(player=p, item='same-item')


@pytest.mark.django_db
def test_UlAddUnlock(Q, auth_header):
    from player.tests import PlayerFactory
    p = PlayerFactory.create()

    rst = Q('''
        mutation TestUlAddUnlock($id: Int!, $item: String!) {
            UlAddUnlock(id: $id, item: $item)
        }
    ''', variables={'id': p.id, 'item': 'reimu-skin-alt'}, headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['UlAddUnlock'] is True
    assert models.Unlocked.objects.filter(player=p, item='reimu-skin-alt').exists()


@pytest.mark.django_db
def test_UlAddUnlock_idempotent(Q, auth_header):
    from player.tests import PlayerFactory
    p = PlayerFactory.create()

    for _ in range(2):
        rst = Q('''
            mutation TestUlAddUnlock($id: Int!, $item: String!) {
                UlAddUnlock(id: $id, item: $item)
            }
        ''', variables={'id': p.id, 'item': 'reimu-skin-alt'}, headers=auth_header)

        assert 'errors' not in rst

    assert models.Unlocked.objects.filter(player=p, item='reimu-skin-alt').count() == 1
