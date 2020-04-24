# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Callable, Optional

# -- third party --
from mypy.nodes import CallExpr, MDEF, MemberExpr, NameExpr, SymbolTableNode, TypeInfo, Var
from mypy.plugin import ClassDefContext, Plugin
from mypy.types import Instance

# -- own --


# -- code --
class UIMetaPlugin(Plugin):

    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:

        if fullname == 'thb.meta.common.ui_meta':
            return self.ui_meta_class_deco_hook

        return None

    # ----- HOOKS -----
    def ui_meta_class_deco_hook(self, ctx: ClassDefContext) -> None:
        if not isinstance(ctx.reason, CallExpr):
            ctx.api.fail('Calling ui_meta without an arg', ctx.reason)
            return

        base = self.lookup_fully_qualified('thb.meta.common.UIMetaBase')
        assert base
        baseti = base.node
        assert isinstance(baseti, TypeInfo)
        baseexpr = NameExpr('UIMetaBase')
        baseexpr.fullname = 'thb.meta.common.UIMetaBase'
        baseexpr.kind = base.kind
        baseexpr.node = baseti
        ctx.cls.base_type_exprs = [baseexpr]
        ctx.cls.info.bases = [Instance(baseti, [])]
        ctx.cls.info.mro.insert(1, baseti)

        expr = ctx.reason.args[0]
        assert isinstance(expr, MemberExpr), expr
        ti = expr.node
        if not ti:
            return

        assert isinstance(ti, TypeInfo), ti

        var = Var('ui_meta', Instance(ctx.cls.info, []))
        var.info = ctx.cls.info
        ti.names[var.name] = SymbolTableNode(MDEF, var)


def plugin(version: str) -> type:
    return UIMetaPlugin
