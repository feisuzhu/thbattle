from django.apps import AppConfig


class RankingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ranking'
    verbose_name = '天梯'
    sort_order = 50
