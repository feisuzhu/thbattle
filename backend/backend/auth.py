# -*- coding: utf-8 -*-

# -- stdlib --
from base64 import b64decode

# -- third party --
from authext.models import User
from django.contrib import auth
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

# -- own --


# -- code --
class TokenAuthMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        uid = None
        request.api_user = AnonymousUser()
        header = request.META.get('HTTP_AUTHORIZATION')

        if not header:
            return self.get_response(request)

        try:
            tag, token = header.split()
        except Exception:
            return self.unauthenticated()

        if tag == 'Basic':
            un, pwd = b64decode(token).decode('utf-8').split(':', 2)
            user = auth.authenticate(username=un, password=pwd)
            if user and user.is_staff:
                request.api_user = user
                return self.get_response(request)

        elif tag == 'Bearer':
            if uid := User.uid_from_token(token):
                request.api_user = SimpleLazyObject(lambda: User.objects.get(id=uid))
                return self.get_response(request)

        return self.unauthenticated()

    def unauthenticated(self):
        return HttpResponse(
            '{"data": null, "errors": [{"message": "Unauthenticated", "locations": []}]}',
            content_type='application/json',
            status=401,
        )
