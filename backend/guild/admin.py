# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- local --
from . import models


# -- code --
@admin.register(models.Guild)
class GuildAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'leader', 'slogan', 'totem', 'founded_at')
    list_filter = ()
    search_fields = ('name', 'leader__username')
    ordering = ('id',)
