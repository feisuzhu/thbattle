# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Optional, cast

# -- third party --
# -- own --
# -- errord --
from mypy.checkmember import bind_self
from mypy.nodes import Decorator, MemberExpr, CallExpr
from mypy.plugin import AttributeContext, MethodSigContext, Plugin
from mypy.types import AnyType, CallableType, Instance, Type, TypeOfAny, UnionType


# -- code --
class BatchListPlugin(Plugin):

    def get_method_signature_hook(self, fullname: str
                                  ) -> Optional[Callable[[MethodSigContext], CallableType]]:
        if fullname == 'utils.misc.BatchList.__call__':
            return batchlist_method_signature_hook

        return None

    def get_attribute_hook(self, fullname: str
                           ) -> Optional[Callable[[AttributeContext], Type]]:
        if fullname.startswith('utils.misc.BatchList'):
            return batchlist_attribute_hook

        return None


def batchlist_attribute_hook(ctx: AttributeContext) -> Type:
    if isinstance(ctx.type, UnionType):
        for i in ctx.type.items:
            if isinstance(i, Instance) and i.type.fullname == 'utils.misc.BatchList':
                instance = i
                break

    elif isinstance(ctx.type, Instance):
        instance = ctx.type

    else:
        assert False, 'WTF?!'

    typeinfo = instance.type

    expr = ctx.context
    if isinstance(expr, MemberExpr):
        is_method = False
        field = expr.name
    elif isinstance(expr, CallExpr):
        is_method = True
        callee = expr.callee
        assert isinstance(callee, MemberExpr)
        field = callee.name
    else:
        assert False, expr

    if field in typeinfo.names:
        t = typeinfo.names[field].type
        assert t
        return t

    typeparam = instance.args[0]
    if not isinstance(typeparam, Instance):
        ctx.api.fail('BatchList[{}] not supported by checker'.format(typeparam), expr)
        return Instance(typeinfo, [AnyType(TypeOfAny.from_error)])

    names = typeparam.type.names

    if field not in names:
        ctx.api.fail(
            'BatchList item {} has no attribute "{}"'.format(
                instance.args[0], field,
            ), expr
        )
        return Instance(typeinfo, [AnyType(TypeOfAny.from_error)])

    stnode = typeparam.type.get(field)
    assert stnode
    node = stnode.node
    typ = stnode.type

    if is_method:
        assert isinstance(typ, CallableType)

        if isinstance(node, Decorator) and node.var.is_classmethod:
            t = bind_self(typ, is_classmethod=True)
        elif isinstance(node, Decorator) and node.var.is_staticmethod:
            t = typ
        else:
            t = bind_self(typ)
    else:
        if isinstance(node, Decorator) and node.var.is_property:
            assert isinstance(typ, CallableType)
            t = typ.ret_type
        else:
            t = typ

    if not t:
        ctx.api.fail(
            f'BatchList item {instance.args[0]} has attribute "{field}" with no annotation', expr
        )
        t = Instance(typeinfo, [AnyType(TypeOfAny.from_error)])

    return Instance(typeinfo, [t])


def batchlist_method_signature_hook(ctx: MethodSigContext) -> CallableType:
    instance = cast(Instance, ctx.type)
    typeinfo = instance.type

    expr = ctx.context

    c = instance.args[0]
    if isinstance(c, CallableType):
        return c.copy_modified(
            ret_type=Instance(typeinfo, [c.ret_type])
        )

    elif isinstance(c, AnyType):
        return ctx.default_signature.copy_modified(
            ret_type=Instance(typeinfo, [AnyType(TypeOfAny.from_another_any, source_any=c)])
        )
    else:
        ctx.api.fail("BatchList item {} is not callable".format(instance.args[0]), expr)
        return ctx.default_signature


def plugin(version: str) -> type:
    return BatchListPlugin
