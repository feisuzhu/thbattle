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
    list_display = ('id', 'name', 'version', 'branch', 'url')
    list_filter = ()
    search_fields = ()
    ordering = ('id',)


@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'text')
    list_filter = ()
    search_fields = ('text',)
    ordering = ('id',)
