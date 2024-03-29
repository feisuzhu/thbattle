import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from utils.misc import BatchList
from typing import Callable, Any


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
