# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Guild)
class GuildAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'founder', 'leader', 'slogan', 'totem', 'founded_at')
    list_filter = ()
    search_fields = ('name', 'founder__username', 'leader__username')
    ordering = ('id',)
