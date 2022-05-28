# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'sku')
    list_filter = ('sku',)
    search_fields = ('player__name',)
    ordering = ('owner',)


@admin.register(models.ItemActivity)
class ItemActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'action', 'sku', 'count', 'extra', 'created_at')
    list_filter = ('action',)
    search_fields = ('player__name', 'item__type')
    ordering = ('player',)


@admin.register(models.ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'count', 'currency', 'price')
    list_filter = ('sku', 'currency')
    search_fields = ('sku',)
    ordering = ('sku',)

    def __str__(self):
        return self.id


# RELATED FILES:
# models.py
