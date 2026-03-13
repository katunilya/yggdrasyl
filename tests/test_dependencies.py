from dataclasses import dataclass

import pytest

from yggdrasyl import (
    Dependencies,
    Injected,
    NotContextManagerError,
    TypeAlreadyRegisteredError,
    TypeNotRegisteredError,
    TypeResolutionError,
    from_factory,
    from_instance,
)


@dataclass
class SyncContextService:
    state: str = "waiting"

    def __enter__(self) -> None:
        self.state = "running"

    def __exit__(self, exc_type, exc, tb):
        self.state = "finished"


@dataclass
class AsyncContextService:
    state: str = "waiting"

    async def __aenter__(self) -> None:
        self.state = "running"

    async def __aexit__(self, exc_type, exc, tb):
        self.state = "finished"


@dataclass
class ExampleService: ...


@pytest.fixture
def deps() -> Dependencies:
    return Dependencies()


def test_default_registration(deps: Dependencies) -> None:
    deps.register(ExampleService, from_factory(ExampleService))

    assert deps.resolve(ExampleService) is deps.resolve(ExampleService)


def test_uncached_registration(deps: Dependencies) -> None:
    deps.register(ExampleService, lambda _: ExampleService(), cached=False)

    assert deps.resolve(ExampleService) is not deps.resolve(ExampleService)


async def test_managed_registration(deps: Dependencies) -> None:
    deps.register(SyncContextService, lambda _: SyncContextService(), managed=True)
    deps.register(AsyncContextService, lambda _: AsyncContextService(), managed=True)

    sync_service = deps.resolve(SyncContextService)
    async_service = deps.resolve(AsyncContextService)

    assert sync_service.state == "waiting"
    assert async_service.state == "waiting"

    async with deps.initialize():
        assert sync_service.state == "running"
        assert async_service.state == "running"

    assert sync_service.state == "finished"
    assert async_service.state == "finished"


def test_register_override(deps: Dependencies) -> None:
    deps.register(int, lambda _: 1)
    assert deps.resolve(int) == 1

    deps.register(int, lambda _: 2, override=True)
    assert deps.resolve(int) == 2


def test_raises_type_already_registered_error(deps: Dependencies) -> None:
    deps.register(int, lambda _: 1)

    with pytest.raises(TypeAlreadyRegisteredError):
        deps.register(int, lambda _: 2)


def test_raises_type_not_registered_error(deps: Dependencies) -> None:
    with pytest.raises(TypeNotRegisteredError):
        deps.resolve(int)


def test_raises_type_resolution_error(deps: Dependencies) -> None:
    deps.register(float, lambda _: 1 / 0)

    with pytest.raises(TypeResolutionError):
        deps.resolve(float)


async def test_raises_not_context_manager_error(deps: Dependencies) -> None:
    deps.register(int, lambda _: 1, managed=True)

    with pytest.raises(NotContextManagerError):
        async with deps.initialize():
            ...


def test_wire(deps: Dependencies) -> None:
    deps.register(int, from_instance(1))
    deps.register(str, from_instance("foo"))

    @deps.wire
    def foo(a: int, x: int = Injected[int], y: str = Injected[str]) -> str:
        return f"{a} {x} {y}"

    assert foo(1) == "1 1 foo"


def test_scope(deps: Dependencies) -> None:
    deps.register(int, lambda _: 1)
    assert deps.resolve(int) == 1

    with deps.scope():
        deps.register(int, lambda _: 2, override=True)
        assert deps.resolve(int) == 2

    assert deps.resolve(int) == 1
