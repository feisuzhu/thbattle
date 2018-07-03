# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import json
import urllib.parse

# -- third party --
import requests

# -- own --
from backend.settings import LeanCloudCredentials
from graphql import GraphQLError


# -- code --
api = requests.Session()
api.headers.update({
    'Content-Type': 'application/json',
    'X-LC-Id': LeanCloudCredentials.APP_ID,
    'X-LC-Key': f'{LeanCloudCredentials.MASTER_KEY},master',
})

BASE = LeanCloudCredentials.URL
urljoin = urllib.parse.urljoin

get     = lambda e, **k: api.get(urljoin(BASE, e), **k).json()
post    = lambda e, data, **k: api.post(urljoin(BASE, e), data=json.dumps(data), **k).json()
put     = lambda e, data, **k: api.put(urljoin(BASE, e), data=json.dumps(data), **k).json()
delete  = lambda e, **k: api.delete(urljoin(BASE, e), **k).json()


def send_smscode(phone):
    post('requestSmsCode', {'mobilePhoneNumber': phone})


def verify_smscode(phone, code):
    return True
    rst = post('verifySmsCode/%s' % code, {'mobilePhoneNumber': phone})

    if rst.get('error'):
        return False
        # raise GraphQLError(rst['error'])

    return True
