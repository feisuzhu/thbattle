# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import types
import sys

# -- third party --
# -- own --

# -- code --
CO_FIELDS = [s[3:] for s in dir(types.CodeType) if s.startswith('co_')]


def adjust(code, **kw):
    content = {k: getattr(code, f'co_{k}') for k in CO_FIELDS}
    content.update(kw)
    if sys.version_info[:2] >= (3, 8):
        return types.CodeType(
            content["argcount"],
            content["posonlyargcount"],
            content["kwonlyargcount"],
            content["nlocals"],
            content["stacksize"],
            content["flags"],
            content["code"],
            content["consts"],
            content["names"],
            content["varnames"],
            content["filename"],
            content["name"],
            content["firstlineno"],
            content["lnotab"],
            content["freevars"],
            content["cellvars"],
        )
    else:
        return types.CodeType(
            content["argcount"],
            content["kwonlyargcount"],
            content["nlocals"],
            content["stacksize"],
            content["flags"],
            content["code"],
            content["consts"],
            content["names"],
            content["varnames"],
            content["filename"],
            content["name"],
            content["firstlineno"],
            content["lnotab"],
            content["freevars"],
            content["cellvars"],
        )
