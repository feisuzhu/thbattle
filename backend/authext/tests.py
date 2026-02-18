# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import auth
import factory
import pytest

# -- own --
from . import models
from system.tests import SMSVerificationFactory


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


@pytest.mark.django_db
def test_login_marks_verification_used(Q):
    phone = PhoneLoginFactory.create(phone="999888")
    SMSVerificationFactory.create(phone=phone.phone, key="aaa111")

    Q('''
        query {
            login {
                phone(smsVerificationKey:"aaa111") { id }
            }
        }
    ''')

    from system.models import SMSVerification
    v = SMSVerification.objects.get(key="aaa111")
    assert v.used is True


@pytest.mark.django_db
def test_login_invalid_verification(Q):
    PhoneLoginFactory.create(phone="123123")

    rst = Q('''
        query {
            login {
                phone(smsVerificationKey:"wrong-key") { id }
            }
        }
    ''')

    assert 'errors' in rst


@pytest.mark.django_db
def test_token_roundtrip():
    u = UserFactory.create()
    proxy = models.User.objects.get(id=u.id)
    token = proxy.token()
    assert token

    recovered = models.User.from_token(token)
    assert recovered is not None
    assert recovered.id == u.id


@pytest.mark.django_db
def test_token_invalid():
    result = models.User.from_token('garbage-token')
    assert result is None


@pytest.mark.django_db
def test_uid_from_token():
    u = UserFactory.create()
    proxy = models.User.objects.get(id=u.id)
    token = proxy.token()

    uid = models.User.uid_from_token(token)
    assert uid == u.id


@pytest.mark.django_db
def test_login_via_token_query(Q):
    phone = PhoneLoginFactory.create(phone="777777")
    SMSVerificationFactory.create(phone=phone.phone, key="tok001")

    rst = Q('''
        query {
            login {
                phone(smsVerificationKey:"tok001") { token }
            }
        }
    ''')

    assert 'errors' not in rst
    token = rst['data']['login']['phone']['token']
    assert token

    rst2 = Q('''
        query TestTokenLogin($token: String!) {
            login {
                token(token: $token) { id }
            }
        }
    ''', variables={'token': token})

    assert 'errors' not in rst2
    assert rst2['data']['login']['token']['id'] == phone.user.id
