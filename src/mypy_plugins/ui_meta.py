# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from typing import Callable, Optional

# -- own --
# -- errord --
from mypy.nodes import CallExpr, MDEF, MemberExpr, SymbolTableNode, TypeInfo, Var
from mypy.plugin import ClassDefContext, Plugin
from mypy.types import Instance


# -- code --
class UIMetaPlugin(Plugin):

    def get_class_decorator_hook(self, fullname: str
                                 ) -> Optional[Callable[[ClassDefContext], None]]:

        if fullname == 'thb.meta.common.ui_meta':
            return ui_meta_class_deco_hook
            print(fullname)

        return None


def ui_meta_class_deco_hook(ctx: ClassDefContext) -> None:
    if not isinstance(ctx.reason, CallExpr):
        ctx.api.fail('Calling ui_meta without an arg', ctx.reason)
        return

    expr = ctx.reason.args[0]
    assert isinstance(expr, MemberExpr), expr
    ti = expr.node
    if not ti:
        return

    assert isinstance(ti, TypeInfo), ti

    var = Var('ui_meta', Instance(ctx.cls.info, []))
    var.info = ctx.cls.info
    ti.names[var.name()] = SymbolTableNode(MDEF, var)


def plugin(version: str) -> type:
    return UIMetaPlugin
