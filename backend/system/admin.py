# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'branch', 'url', 'chat')
    list_filter = ()
    search_fields = ()
    ordering = ('id',)


@admin.register(models.Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    list_filter = ()
    search_fields = ()
    ordering = ('key',)


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'text')
    list_filter = ()
    search_fields = ('text',)
    ordering = ('id',)


@admin.register(models.SMSVerification)
class SMSVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'key', 'used')
    ordering = ('-id',)
