# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.PhoneLogin)
class PhoneLoginAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone')
    list_filter = ()
    search_fields = ()
