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

    name = factory.Sequence(lambda n: f'pack-{n}')


class EmojiFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Emoji

    pack = factory.SubFactory(EmojiPackFactory)
    name = factory.Sequence(lambda n: f'emoji-{n}')
    url  = factory.LazyAttribute(lambda o: f'http://example.com/{o.name}.png')


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


@pytest.mark.django_db
def test_emoji_packs_query(Q, auth_header):
    from player.tests import PlayerFactory
    PlayerFactory.create()

    pack = EmojiPackFactory.create(name='Touhou Pack')
    EmojiFactory.create(pack=pack, name='reimu')
    EmojiFactory.create(pack=pack, name='marisa')

    rst = Q('''
        query TestEmojiPacks($ids: [Int!]!) {
            emojiPacks(ids: $ids) { id name }
        }
    ''', variables={'ids': [pack.id]}, headers=auth_header)

    assert 'errors' not in rst
    assert len(rst['data']['emojiPacks']) == 1
    assert rst['data']['emojiPacks'][0]['name'] == 'Touhou Pack'


@pytest.mark.django_db
def test_emojis_query(Q, auth_header):
    from player.tests import PlayerFactory
    PlayerFactory.create()

    pack = EmojiPackFactory.create()
    e1 = EmojiFactory.create(pack=pack, name='smile')
    e2 = EmojiFactory.create(pack=pack, name='cry')

    rst = Q('''
        query TestEmojis($ids: [Int!]!) {
            emojis(ids: $ids) { id name url }
        }
    ''', variables={'ids': [e1.id, e2.id]}, headers=auth_header)

    assert 'errors' not in rst
    names = {e['name'] for e in rst['data']['emojis']}
    assert names == {'smile', 'cry'}


@pytest.mark.django_db
def test_fixed_text_empty_query(Q, auth_header):
    from player.tests import PlayerFactory
    PlayerFactory.create()

    rst = Q('''
        query {
            fixedTexts(ids: [999]) { id }
        }
    ''', headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['fixedTexts'] == []
