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
def test_login(Q):
    from authext.tests import PhoneLoginFactory
    PhoneLoginFactory.create(phone="123123")

    rst = Q('''
        query {
            login {
                phone(phone: "123123", code:"123123") {
                    token
                }
            }
        }
        '''
    )

    assert 'errors' not in rst
    assert rst['data']['login']['phone']
