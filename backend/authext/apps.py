from django.apps import AppConfig


class AuthExtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authext'
    verbose_name = '认证和授权'
    sort_order = 20
