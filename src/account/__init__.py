# -*- coding: utf-8 -*-

from settings import ACCOUNT_MODULE
exec 'from %s import *' % ACCOUNT_MODULE
