# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory
import pytest

# -- own --
from . import models


# -- code --
class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Item

    owner = factory.SubFactory('player.tests.PlayerFactory')
    sku   = factory.Sequence(lambda n: f'item-{n}')
    count = 1


@pytest.mark.django_db
def test_item_creation():
    item = ItemFactory.create(sku='potion', count=5)
    assert item.sku == 'potion'
    assert item.count == 5
    assert item.owner is not None


@pytest.mark.django_db
def test_item_str():
    item = ItemFactory.create(sku='gem')
    assert 'gem' in str(item)


@pytest.mark.django_db
def test_item_per_player_unique():
    from player.tests import PlayerFactory
    p = PlayerFactory.create()
    ItemFactory.create(owner=p, sku='unique-item')

    with pytest.raises(Exception):
        ItemFactory.create(owner=p, sku='unique-item')


@pytest.mark.django_db
def test_item_same_sku_different_players():
    item1 = ItemFactory.create(sku='shared-sku')
    item2 = ItemFactory.create(sku='shared-sku')
    assert item1.owner != item2.owner
