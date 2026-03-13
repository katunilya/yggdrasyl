from typing import Callable

from ._dependencies import _FactoryFn


def from_instance[T](obj: T) -> _FactoryFn[T]:
    return lambda _: obj


def from_factory[T](fn: Callable[[], T]) -> _FactoryFn[T]:
    return lambda _: fn()
