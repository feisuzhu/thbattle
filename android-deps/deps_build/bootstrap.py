# -*- coding: utf-8 -*-

# -- stdlib --
from pathlib import Path
from typing import Optional
import os
import sys

# -- third party --
# -- own --
from .escapes import escape_codes


# -- code --
def is_in_venv() -> bool:
    """
    Are we in a virtual environment?
    """
    return hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)


def get_cache_home() -> Path:
    """
    Get the cache home directory. All intermediate files should be stored here.
    """
    return Path.home() / ".cache" / "thb-android-deps"


_Environ = os.environ.__class__

_CHANGED_ENV = {}


class _EnvironWrapper(_Environ):
    def __setitem__(self, name: str, value: str) -> None:
        orig = self.get(name, None)
        _Environ.__setitem__(self, name, value)
        new = self[name]
        self._print_diff(name, orig, new)

    def __delitem__(self, name: str) -> None:
        orig = self.get(name, None)
        _Environ.__delitem__(self, name)
        new = self.get(name, None)
        self._print_diff(name, orig, new)

    def pop(self, name: str, default: Optional[str] = None) -> Optional[str]:
        orig = self.get(name, None)
        value = _Environ.pop(self, name, default)
        new = self.get(name, None)
        self._print_diff(name, orig, new)
        return value

    def _print_diff(self, name, orig, new):
        G = escape_codes["bold_green"]
        R = escape_codes["bold_red"]
        N = escape_codes["reset"]

        if orig == new:
            return

        _CHANGED_ENV[name] = new

        p = lambda v: print(v, file=sys.stderr, flush=True)

        if orig == None:
            p(f"{G}:: ENV+ {name}={new}{N}")
        elif new == None:
            p(f"{R}:: ENV- {name}={orig}{N}")
        elif orig in new:
            idx = new.index(orig)
            l = len(orig)
            p(f"{G}:: ENV{N} {name}={G}{new[:idx]}{N}{new[idx:idx+l]}{G}{new[idx+l:]}{N}")
        else:
            p(f"{R}:: ENV- {name}={orig}{N}")
            p(f"{G}:: ENV+ {name}={new}{N}")

    def get_changed_envs(self):
        return dict(_CHANGED_ENV)


def monkey_patch_environ():
    """
    Monkey patch os.environ to print changes.
    """
    os.environ.__class__ = _EnvironWrapper


def early_init():
    """
    Do early initialization.
    This must be called before any other non-stdlib imports.
    """
    monkey_patch_environ()
