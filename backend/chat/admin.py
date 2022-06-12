# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.FixedText)
class FixedTextAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'character', 'actor')
    list_filter = ('character',)
    search_fields = ('text',)
    ordering = ('-id',)
    sort_order = 10


@admin.register(models.SharedFixedText)
class SharedFixedTextAdmin(admin.ModelAdmin):
    list_display = ('ref',)
    sort_order = 20


@admin.register(models.Emoji)
class EmojiAdmin(admin.ModelAdmin):
    list_display = ('id', 'pack', 'name', 'url')
    list_filter = ('pack',)
    search_fields = ('name', 'pack__name')
    ordering = ('-id',)
    sort_order = 30


@admin.register(models.EmojiPack)
class EmojiPackAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    filter_horizontal = ('avail_to',)
    ordering = ('-id',)
    sort_order = 40


@admin.register(models.SharedEmojiPack)
class SharedEmojiPackAdmin(admin.ModelAdmin):
    list_display = ('ref',)
    sort_order = 50
