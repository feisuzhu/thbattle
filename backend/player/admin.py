# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
# Register your models here.

@admin.register(models.Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'level', 'exp', 'games', 'drops', 'up', 'bomb', 'point')
    list_filter = ()
    search_fields = ('name',)
    filter_horizontal = ('badges', 'friends', 'blocks')
    ordering = ('user',)


@admin.register(models.Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'suspect', 'reason', 'detail', 'game_id', 'reported_at', 'outcome')
    list_filter = ('reason',)
    search_fields = ('reporter', 'suspect', 'reason')
