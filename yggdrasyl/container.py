import functools
import inspect
from dataclasses import dataclass, field
from typing import Callable, Protocol, Type, get_type_hints


class Resolver[T](Protocol):
    def __call__(self) -> T:
        raise NotImplementedError


class InstanceResolver[T](Resolver[T]):
    def __init__(self, instance: T) -> None:
        self._instance = instance

    def __call__(self) -> T:
        return self._instance


class FactoryResolver[**P, T](Resolver[T]):
    def __init__(
        self,
        container: "Container",
        factory: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self._factory = container.wire(factory)
        self._args = args
        self._kwargs = kwargs

    def __call__(self) -> T:
        return self._factory(*self._args, **self._kwargs)


class CachedFactoryResolver[**P, T](Resolver[T]):
    def __init__(
        self,
        container: "Container",
        factory: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self._factory = container.wire(factory)
        self._args = args
        self._kwargs = kwargs
        self._cache: T | None = None

    def __call__(self) -> T:
        if not self._cache:
            self._cache = self._factory(*self._args, **self._kwargs)

        return self._cache


class LazyResolver[T](Resolver[T]):
    def __init__(
        self,
        container: "Container",
        dependency_type: Type[T],
    ) -> None:
        self._container = container
        self._dependency_type = dependency_type

    def __call__(self) -> T:
        return self._container.resolve(self._dependency_type)


class Injected: ...


@dataclass(slots=True)
class Container:
    _type_registry: dict[Type, Resolver] = field(default_factory=dict)
    _name_registry: dict[str, Resolver] = field(default_factory=dict)

    @dataclass(slots=True)
    class DependencyBuilder[T]:
        _container: "Container"
        _dependency_type: Type[T]

        def as_instance(self, instance: T) -> "Container":
            _resolver = InstanceResolver(instance)
            self._container._type_registry[self._dependency_type] = _resolver

            return self._container

        def as_factory[**P](
            self,
            factory: Callable[P, T],
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> "Container":
            _resolver = FactoryResolver(self._container, factory, *args, **kwargs)
            self._container._type_registry[self._dependency_type] = _resolver

            return self._container

        def as_cached_factory[**P](
            self,
            factory: Callable[P, T],
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> "Container":
            _resolver = CachedFactoryResolver(
                self._container,
                factory,
                *args,
                **kwargs,
            )
            self._container._type_registry[self._dependency_type] = _resolver

            return self._container

    def register[T](self, dependency_type: Type[T]) -> "Container.DependencyBuilder[T]":
        return Container.DependencyBuilder(
            self,
            dependency_type,
        )

    def resolve[T](self, dependency_type: Type[T]) -> T:
        if dependency_type not in self._type_registry:
            raise KeyError(f"dependency not found: type={dependency_type}")

        return self._type_registry[dependency_type]()

    def _get_resolver[T](
        self,
        dependency_type: Type[T],
    ) -> Resolver[T]:
        return LazyResolver(
            container=self,
            dependency_type=dependency_type,
        )

    def wire[**P, R](self, func: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(func)
        hints = get_type_hints(func)

        injected_kwargs = dict[str, Resolver]()

        for param_name, param in signature.parameters.items():
            if param.default is not Injected:
                continue

            if param.kind != param.KEYWORD_ONLY:
                raise Exception(f"{func.__name__}:{param_name} must be kw only")

            dependency_type = (
                param.annotation
                if not isinstance(param.annotation, str)
                else hints[param_name]
            )

            injected_kwargs[param_name] = self._get_resolver(dependency_type)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for param_name, _resolver in injected_kwargs.items():
                if param_name not in kwargs:
                    kwargs[param_name] = _resolver()

            return func(*args, **kwargs)

        return wrapper
