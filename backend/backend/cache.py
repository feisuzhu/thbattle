from django.conf import settings
import redis

rdb = redis.from_url(settings.REDIS_URL)
