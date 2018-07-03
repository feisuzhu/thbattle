# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models
from django.contrib.auth.admin import UserAdmin as OriginalUserAdmin


# -- code --
# Register your models here.

@admin.register(models.User)
class UserAdmin(OriginalUserAdmin):
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2'),
        }),
    )
    list_display = ('id', 'phone', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('phone',)
    ordering = ('phone',)


@admin.register(models.Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'guild', 'ppoint', 'jiecao', 'games', 'drops')
    list_filter = ()
    search_fields = ('user__phone', 'name', 'guild__name')
    filter_horizontal = ('badges', 'friends', 'blocks')
    ordering = ('user',)


@admin.register(models.Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'suspect', 'reason', 'detail', 'game_id', 'reported_at', 'outcome')
    list_filter = ('reason',)
    search_fields = ('reporter', 'suspect', 'reason')
