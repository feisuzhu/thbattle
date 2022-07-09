# -*- coding: utf-8 -*-

# -- stdlib --
import base64
import logging
import re

# -- third party --
from django.conf import settings
from django.db import models
import django.contrib.auth.models as auth_models
import itsdangerous
import msgpack

# -- own --

# -- code --
log = logging.getLogger("authext.model")
_ = lambda s: {'help_text': s, 'verbose_name': s}


def is_phone_number(value):
    if not isinstance(value, str):
        return False

    return bool(re.match(r'^(?!17[01])\d{11}$', value))


class User(auth_models.User):
    class Meta:
        proxy = True
        verbose_name        = '用户'
        verbose_name_plural = '用户'

    token_signer = itsdangerous.TimestampSigner(settings.SECRET_KEY)

    def token(self):
        data = base64.b64encode(msgpack.dumps({'type': 'user', 'id': self.id}))
        return self.token_signer.sign(data).decode('utf-8')

    @classmethod
    def uid_from_token(cls, token, max_age=30 * 86400):
        try:
            data = cls.token_signer.unsign(token.encode('utf-8'), max_age=max_age)
        except Exception as e:
            log.info("User.from_token unsign failed: %s", e)
            return None

        data = msgpack.loads(base64.b64decode(data))
        if data.get('type') != 'user':
            return None

        return data['id']

    @classmethod
    def from_token(cls, token, max_age=30 * 86400):
        uid = cls.uid_from_token(token, max_age) or None
        return uid and cls.objects.filter(id=uid).first()


class Group(auth_models.Group):
    class Meta:
        proxy = True
        verbose_name        = '组'
        verbose_name_plural = '组'


class PhoneLogin(models.Model):

    class Meta:
        verbose_name        = '手机登录'
        verbose_name_plural = '手机登录'

    id    = models.AutoField(**_('ID'), primary_key=True)
    user  = models.OneToOneField(User, models.CASCADE, **_('用户'), unique=True)
    phone = models.CharField(**_('手机号'), unique=True, max_length=15, validators=[is_phone_number])
