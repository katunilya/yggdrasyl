from typing import Callable, get_type_hints

from ._dependencies import Dependencies, _FactoryFn


def from_instance[T](obj: T) -> _FactoryFn[T]:
    return lambda _: obj


def from_factory[T](fn: Callable[..., T]) -> _FactoryFn[T]:
    _types = {
        name: type_ for name, type_ in get_type_hints(fn).items() if name != "return"
    }

    if not _types:
        return lambda _: fn()

    def _factory(d: Dependencies) -> T:
        _args = {}

        for _arg_name, _arg_type in _types.items():
            d.requires(_arg_type)
            _args[_arg_name] = d.resolve(_arg_type)

        return fn(**_args)

    return _factory
