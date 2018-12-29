# -*- coding: utf-8 -*-

# -- stdlib --
import sys

# -- third party --
# -- own --


# -- code --
class ViralContext(object):
    VIRAL_SEARCH = ['self']
    _viral_mro_cache = None

    def __new__(cls, *a, **k):
        self = object.__new__(cls)
        cache = cls._viral_mro_cache if '_viral_mro_cache' in cls.__dict__ else None
        if not cache:
            cache = [c for c in cls.mro() if ViralContext in c.__bases__]
            cls._viral_mro_cache = cache

        for c in cache:
            that = c.viral_search(start=2) if cls.VIRAL_SEARCH else None
            c.viral_import(self, that.viral_export() if that else None)

        return self

    @classmethod
    def viral_search(cls, start=1):
        f = sys._getframe(start)
        while f:
            for name in cls.VIRAL_SEARCH:
                that = f.f_locals.get(name)
                if that is not None and isinstance(that, cls):
                    return that

            f = f.f_back

        return None

    def viral_import(self, env):
        raise Exception('Override this!')

    def viral_export(self):
        raise Exception('Override this!')
