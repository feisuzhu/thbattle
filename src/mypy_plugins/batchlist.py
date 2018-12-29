# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Optional, cast

# -- third party --
# -- own --
# -- errord --
from mypy.checkmember import bind_self
from mypy.nodes import Decorator, MemberExpr, SYMBOL_FUNCBASE_TYPES
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
            if isinstance(i, Instance) and i.type.fullname() == 'utils.misc.BatchList':
                instance = i
                break

    elif isinstance(ctx.type, Instance):
        instance = ctx.type

    else:
        assert False, 'WTF?!'

    typeinfo = instance.type

    expr = ctx.context
    assert isinstance(expr, MemberExpr), expr

    field = expr.name

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

    if isinstance(node, SYMBOL_FUNCBASE_TYPES):
        assert isinstance(typ, CallableType)
        t = bind_self(typ)
    elif isinstance(node, Decorator) and node.var.is_classmethod:
        assert isinstance(typ, CallableType)
        t = bind_self(typ, is_classmethod=True)
    elif isinstance(node, Decorator) and node.var.is_staticmethod:
        assert isinstance(typ, CallableType)
        t = typ
    elif isinstance(node, Decorator) and node.var.is_property:
        assert isinstance(typ, CallableType)
        t = typ.ret_type
    elif isinstance(node, Decorator) and isinstance(typ, CallableType):
        t = bind_self(typ)
    else:
        t = typ
        if not t:
            ctx.api.fail(
                'BatchList item {} has attribute "{}" with no annotation'.format(
                    instance.args[0], field,
                ), expr
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
