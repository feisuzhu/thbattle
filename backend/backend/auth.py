# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
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
        bearer = request.META.get('HTTP_AUTHORIZATION')

        if not bearer:
            request.api_user = AnonymousUser()
            return self.get_response(request)

        while True:
            try:
                tag, token = bearer.split()
            except Exception:
                break

            if tag != 'Bearer':
                break

            from player.models import User
            uid = User.uid_from_token(token)

            break

        if uid is None:
            return HttpResponse('{}', content_type='application/json', status=401)
        else:
            request.api_user = SimpleLazyObject(lambda: User.objects.get(uid))

        return self.get_response(request)
