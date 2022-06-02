# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import factory

# -- own --
from . import models
from authext.tests import UserFactory


# -- code --
class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Player

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('name')
