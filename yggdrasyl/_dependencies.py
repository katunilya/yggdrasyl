from __future__ import annotations

import functools
import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Callable,
    ChainMap,
    Final,
    Generator,
    MutableMapping,
    Self,
    Type,
    cast,
)

from ._errors import (
    NotContextManagerError,
    TypeAlreadyRegisteredError,
    TypeNotRegisteredError,
    TypeResolutionError,
)

_NOT_SET: Final[object] = object()


type _FactoryFn[T] = Callable[[Dependencies], T]


class _InjectionMarker:  # pragma: no cover
    def __getitem__[T](self, _: Type[T]) -> T:
        return cast(T, self)

    def __setitem__(self, key, value) -> None: ...


Injected = _InjectionMarker()


@dataclass(slots=True)
class _Resolver[T]:
    resolver: _FactoryFn[T]
    cached: bool
    managed: bool

    _cached_instance: T = field(
        init=False,
        default=_NOT_SET,
        repr=False,
    )  # type: ignore

    def __call__(self, deps: Dependencies) -> T:
        if not self.cached:
            return self.resolver(deps)

        if self._cached_instance is _NOT_SET:
            self._cached_instance = self.resolver(deps)

        return self._cached_instance


_UNSET: Final[object] = object()


@dataclass(slots=True)
class Dependencies:
    _registry_context_var: ContextVar[MutableMapping[Type[Any], _Resolver[Any]]] = (
        field(
            init=False,
            default=_UNSET,
            repr=False,
        )
    )  # ty: ignore[invalid-assignment]

    @property
    def _registry(self) -> MutableMapping[Type[Any], _Resolver[Any]]:
        if self._registry_context_var is _UNSET:
            self._registry_context_var = ContextVar(
                f"yggdrasyl_dependencies_registry_context_var_{id(self)}",
                default=ChainMap(),  # ty: ignore[call-non-callable]
            )

        return self._registry_context_var.get()

    def register[T](
        self,
        /,
        type_: Type[Any],
        resolver: _FactoryFn[T],
        *,
        cached: bool = True,
        managed: bool = False,
        override: bool = False,
    ) -> Self:
        if type_ in self._registry and not override:
            raise TypeAlreadyRegisteredError(type_)

        self._registry[type_] = _Resolver(
            resolver,
            cached=cached,
            managed=managed,
        )

        return self

    def resolve[T](self, /, type_: Type[T]) -> T:
        if type_ not in self._registry:
            raise TypeNotRegisteredError(type_)

        try:
            return self._registry[type_](self)
        except Exception as exc:
            raise TypeResolutionError(type_) from exc

    def wire[**P, R](self, fn: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(fn)

        injected_types = dict[str, Type[Any]]()

        for param_name, param in signature.parameters.items():
            if isinstance(param.default, _InjectionMarker):
                injected_types[param_name] = param.annotation

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for param_name, param_type in injected_types.items():
                if param_name not in kwargs:  # pragma: no cover
                    kwargs[param_name] = self.resolve(param_type)

            return fn(*args, **kwargs)

        return wrapper

    @asynccontextmanager
    async def initialize(self) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            for resolver in self._registry.values():  # pragma: no cover
                if resolver.managed:
                    dependency = resolver(self)

                    if hasattr(dependency, "__aenter__") and hasattr(
                        dependency, "__aexit__"
                    ):
                        await stack.enter_async_context(dependency)
                    elif hasattr(dependency, "__enter__") and hasattr(
                        dependency, "__exit__"
                    ):
                        stack.enter_context(dependency)
                    else:
                        raise NotContextManagerError(dependency)

            yield

    @contextmanager
    def scope(self) -> Generator[Self, Any, None]:
        token = self._registry_context_var.set(
            ChainMap({}, self._registry),  # ty: ignore[call-non-callable]
        )

        try:
            yield self
        finally:
            self._registry_context_var.reset(token)


deps: Final[Dependencies] = Dependencies()
