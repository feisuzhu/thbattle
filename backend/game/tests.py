# Create a fixture using the graphql_query helper and `client` fixture from `pytest-django`.
import json
import pytest
import factory
from graphene_django.utils.testing import graphql_query
import player


class UserFactory(factory.Factory):
    class Meta:
        model = player.models.User

    phone = factory.Faker('phone_number')
    is_superuser = True
    is_staff = True


class PlayerFactory(factory.Factory):
    class Meta:
        model = player.models.Player

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('name')


@pytest.fixture
def auth_header():
    import itsdangerous
    import backend
    import msgpack
    import base64
    signer = itsdangerous.TimestampSigner(backend.settings.SECRET_KEY)
    data = base64.b64encode(msgpack.dumps({'type': 'user', 'id': 1}))
    tok = signer.sign(data).decode('utf-8')
    return {'HTTP_AUTHORIZATION': f'Bearer {tok}'}


@pytest.fixture
def Q(client):

    def func(*args, **kwargs):
        return graphql_query(*args, **kwargs, client=client, graphql_url='/graphql')

    return func


# Test you query using the Q fixture
def test_GmAllocGameId(Q):
    response = Q('''
        mutation {
            GmAllocGameId
        }
        '''
    )

    content = json.loads(response.content)
    assert content['data']['GmAllocGameId'] > 0
    assert 'errors' not in content


@pytest.mark.django_db
def test_GmArchive(Q, auth_header):
    p = PlayerFactory.create()
    p.user.save()
    p.save()

    p = PlayerFactory.create()
    p.user.save()
    p.save()

    import random
    gid = random.randint(100, 10000000)
    game = {
        'gameId': gid,
        'name': 'foo!',
        'type': 'THBattle2v2',
        'flags': {},
        'players': [1, 2],
        'winners': [1],
        'deserters': [2],
        'startedAt': '2020-12-02T15:43:05Z',
        'duration': 333,
    }

    response = Q('''
        mutation TestGmArchive($game: GameInput!) {
            GmArchive(game: $game, archive: "AAAA") {
                id
            }
        }
    ''', variables={'game': game}, headers=auth_header)

    content = json.loads(response.content)
    assert 'errors' not in content
    assert content['data']['GmArchive']['id'] == gid
