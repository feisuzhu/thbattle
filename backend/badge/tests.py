# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory
import pytest

# -- own --
from . import models


# -- code --
class BadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Badge

    title       = factory.Sequence(lambda n: f'badge-{n}')
    description = factory.Faker('sentence')
    icon        = 'icon.png'
    icon2x      = 'icon2x.png'


class PlayerBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PlayerBadge

    player = factory.SubFactory('player.tests.PlayerFactory')
    badge  = factory.SubFactory(BadgeFactory)


@pytest.mark.django_db
def test_badge_str():
    b = BadgeFactory.create(title='勇者')
    assert str(b) == '勇者'


@pytest.mark.django_db
def test_player_badge_creation():
    pb = PlayerBadgeFactory.create()
    assert pb.player is not None
    assert pb.badge is not None
    assert pb.granted_at is not None


@pytest.mark.django_db
def test_player_badge_str():
    from player.tests import PlayerFactory
    p = PlayerFactory.create(name='TestPlayer')
    b = BadgeFactory.create(title='Heroic')
    pb = PlayerBadgeFactory.create(player=p, badge=b)
    assert str(pb) == 'TestPlayer - Heroic'
