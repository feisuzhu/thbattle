# -- stdlib --
# -- third party --
from django.apps import AppConfig

# -- own --

# -- code --
class GameConfig(AppConfig):
    name = 'game'
    verbose_name = '游戏'
    sort_order = 40
