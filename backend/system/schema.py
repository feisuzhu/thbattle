# -*- coding: utf-8 -*-

# -- stdlib --
import base64
import random
import io

# -- third party --
from graphene_django.types import DjangoObjectType
import graphene as gh
import qrcode

# -- own --
from . import models


# -- code --
class Server(DjangoObjectType):
    class Meta:
        model = models.Server

    status = gh.String(required=True, description="服务器状态")

    @staticmethod
    def resolve_status(root, info):
        return "fluent"


class News(DjangoObjectType):
    class Meta:
        model = models.News


class Setting(DjangoObjectType):
    class Meta:
        model = models.Setting


class SMSVerification(DjangoObjectType):
    class Meta:
        model = models.SMSVerification


# ------------------------
class SystemQuery(gh.ObjectType):
    servers = gh.List(
        gh.NonNull(Server),
        description="获取服务器列表",
        required=True,
    )

    @staticmethod
    def resolve_servers(root, info):
        return models.Server.objects.all()

    setting = gh.String(
        key=gh.String(required=True),
        description="获取全局设置",
    )

    @staticmethod
    def resolve_setting(root, info, key):
        r = models.Setting.objects.get(key=key)
        return r and r.value

    news = gh.String(description="获取当前新闻")

    @staticmethod
    def resolve_news(root, info):
        r = models.News.objects.order_by('-id').first()
        return r.text if r else ''

    sms_verification = gh.Field(
        SMSVerification,
        key=gh.String(required=True),
        description="获取短信验证码",
    )

    @staticmethod
    def resolve_sms_verification(root, info, key):
        return models.SMSVerification.objects.filter(key=key).first()


class RequestSMSVerification(gh.Mutation):
    key = gh.String(required=True)
    send_to = gh.String(required=True)
    qr_code = gh.String(required=True, description="二维码")

    @staticmethod
    def mutate(root, info):
        key = hex(random.getrandbits(64))[2:]
        send_to = models.Setting.objects.get(key='sms-verification-receiver').value
        r = models.SMSVerification.objects.create(key=key)
        r.save()

        url = f'http://file.thbattle.cn/pages/send-sms.html?s={key}&n={send_to}'
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)

        buf = io.BytesIO()
        qr.make_image().save(buf, format='PNG')
        b = buf.getvalue()

        qr_code = base64.b64encode(b).decode('utf-8')
        return RequestSMSVerification(key=key, send_to=send_to, qr_code=qr_code)


class SystemOps(gh.ObjectType):
    SyRequestSmsVerification = RequestSMSVerification.Field(required=True, description="请求短信验证码")
