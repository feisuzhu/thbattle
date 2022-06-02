# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from graphene_django.utils.testing import graphql_query
import pytest

# -- own --


# -- code --
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
