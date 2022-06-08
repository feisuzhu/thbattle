# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin
import django.contrib.auth.admin as auth_admin
import django.contrib.auth.models as auth_models

# -- own --
from . import models
from player import models as player_models


# -- code --
admin.site.unregister(auth_models.User)
admin.site.unregister(auth_models.Group)


class PlayerInline(admin.StackedInline):
    model = player_models.Player
    can_delete = False
    verbose_name  = '玩家'
    verbose_name_plural = '玩家'


@admin.register(models.User)
class UserAdmin(auth_admin.UserAdmin):
    inlines = (PlayerInline,)
    sort_order = 5


@admin.register(models.Group)
class GroupAdmin(auth_admin.GroupAdmin):
    sort_order = 10


@admin.register(models.PhoneLogin)
class PhoneLoginAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    list_filter = ()
    search_fields = ()
