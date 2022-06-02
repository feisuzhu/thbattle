# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import auth
import factory

# -- own --


# -- code --
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth.models.User

    username = factory.Faker('user_name')
    is_superuser = True
    is_staff = True
