# -*- coding: utf-8 -*-

# -- stdlib --
import datetime

# -- third party --
import factory

# -- own --
from . import models


# -- code --
class SMSVerificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SMSVerification

    phone = factory.Faker("phone_number")
    key   = factory.Faker("md5")
    time  = factory.LazyAttribute(lambda o: datetime.datetime.now())
    used  = False
