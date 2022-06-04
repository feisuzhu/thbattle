# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import auth
import factory
import pytest

# -- own --
from . import models


# -- code --
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth.models.User

    username = factory.Faker('user_name')
    is_superuser = True
    is_staff = True


class PhoneLoginFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PhoneLogin

    user = factory.SubFactory(UserFactory)
    phone = factory.Faker("phone_number")


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
