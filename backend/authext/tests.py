# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import auth
import factory
from system.tests import SMSVerificationFactory
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
    phone = PhoneLoginFactory.create(phone="123123")
    SMSVerificationFactory.create(phone=phone.phone, key="456456")

    rst = Q('''
        query {
            login {
                phone(smsVerificationKey:"456456") {
                    token
                    id
                }
            }
        }
        '''
    )

    assert 'errors' not in rst
    assert rst['data']['login']['phone']['id'] == phone.id
