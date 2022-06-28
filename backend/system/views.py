# -*- coding: utf-8 -*-

# -- stdlib --
import json

# -- third party --
from django.http import JsonResponse
# -- own --
from .models import SMSVerification


# -- code --
def sms_verification(request):
    if not request.api_user.has_perm('system.change_smsverification'):
        print(request.api_user)
        return JsonResponse({'status': 'error', 'message': '没有权限'})

    data = json.loads(request.body)
    phone = data['sender']
    if phone.startswith('+86'):
        phone = phone[3:]

    r = SMSVerification.objects.filter(key=data['text']).first()
    if not r or r.used or r.phone:
        return JsonResponse({'status': 'error', 'message': '验证码错误'})

    r.phone = phone
    r.save()
    return JsonResponse({'status': 'ok'})
