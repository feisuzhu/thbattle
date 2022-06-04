# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.contrib import admin

# -- own --
from . import models


# -- code --
@admin.register(models.Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('id', 'player', 'season', 'category', 'changes', 'mu', 'sigma')
    list_filter = ()
    search_fields = ()
    # ordering = ('-season', '', ')


@admin.register(models.RankingHistory)
class RankingHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'player', 'season', 'score_before', 'score_after')
    list_filter = ()
    search_fields = ()
