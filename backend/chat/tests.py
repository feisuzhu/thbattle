# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory
import pytest

# -- own --
from . import models


# -- code --
class FixedTextFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FixedText

    text = factory.Faker('address')
    actor = factory.Faker('name')


class SharedFixedTextFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SharedFixedText


class EmojiPackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EmojiPack

    text = factory.Faker('lorem')
    actor = factory.Faker('name')


@pytest.mark.django_db
def test_fixed_text_query(Q, auth_header):
    from player.tests import PlayerFactory
    p1 = PlayerFactory.create()
    p2 = PlayerFactory.create()

    a = FixedTextFactory.create()
    b = FixedTextFactory.create()
    c = FixedTextFactory.create()

    SharedFixedTextFactory.create(ref=a)
    b.avail_to.add(p1)
    b.save()
    c.avail_to.add(p2)
    c.save()

    rst = Q('''
        query {
            fixedTexts(ids: [1, 2, 3]) { id canUse(pid: 1) }
        }
        ''', headers=auth_header
    )

    assert 'errors' not in rst
    texts = {t['id']: t for t in rst['data']['fixedTexts']}
    assert texts[1]['canUse']
    assert texts[2]['canUse']
    assert not texts[3]['canUse']
