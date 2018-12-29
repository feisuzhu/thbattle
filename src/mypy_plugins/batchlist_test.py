from utils.misc import BatchList
from typing import Type, Callable, Any


def deco(f) -> Callable[[Any, int], int]:
    return lambda self, b: 1


class A:
    def foo(self, a: int) -> str:
        return ''

    @classmethod
    def bar(cls, a: int) -> str:
        return ''

    @staticmethod
    def baz(a: int) -> str:
        return ''

    @deco
    def meh(self, a: int) -> str:
        return ''

    @property
    def aha(self) -> str:
        return ''

    moo = 1

    def __init__(self) -> None:
        self.mua = 2


a = BatchList[A]([A(), A()])
reveal_type(a.foo)
reveal_type(a.bar)
reveal_type(a.baz)
reveal_type(a.meh)
reveal_type(a.aha)
reveal_type(a.moo)
reveal_type(a.mua)
