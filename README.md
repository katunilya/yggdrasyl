# yggdrasyl

Yggdrasyl is a small, explicit dependency-injection library for Python. It registers
dependencies by type and resolves or injects them into application code.

> Why `yggdrasyl`? The name intentionally misspells Yggdrasil, the tree that connects
> the worlds in Norse mythology—much like a dependency-injection container connects
> application components.

## Installation

Yggdrasyl requires Python 3.13 or newer.

```bash
uv add yggdrasyl
# or
pip install yggdrasyl
```

## Quick start

Create an isolated `Dependencies` container, register factories, and resolve objects by
type. The package also exports `deps`, a module-level container for applications that
prefer a shared registry.

```python
from dataclasses import dataclass

from yggdrasyl import Dependencies, from_factory


@dataclass
class Config:
    api_url: str = "https://example.com"


class Client:
    def __init__(self, config: Config) -> None:
        self.config = config


deps = Dependencies()
deps.register(Config, from_factory(Config))
deps.register(Client, lambda registry: Client(registry.resolve(Config)))

client = deps.resolve(Client)
assert client.config.api_url == "https://example.com"
```

## Registration and resolution

`Dependencies.register(type_, resolver, *, cached=True, managed=False,
override=False)` accepts a type and a resolver function. The resolver receives the
current `Dependencies` container and returns an instance of the registered type.

- `cached=True` reuses the first instance created for that registration. Set it to
  `False` to call the resolver on every resolution.
- `managed=True` makes `initialize()` enter the resolved sync or async context manager.
- `override=True` replaces an existing registration. Otherwise, registering the same
  type raises `TypeAlreadyRegisteredError`.

Use `from_instance(value)` for an existing object and `from_factory(factory)` for a
zero-argument callable:

```python
from yggdrasyl import Dependencies, from_factory, from_instance

deps = Dependencies()
deps.register(int, from_instance(1))
deps.register(list, from_factory(list))
```

`Dependencies.resolve(type_)` returns the registered value. It raises
`TypeNotRegisteredError` when the type is missing and wraps resolver failures in
`TypeResolutionError`.

## Managed dependencies

Entering the asynchronous `initialize()` context resolves every `managed=True`
registration and enters sync and async context managers. Resources are closed when the
context exits. A managed value that implements neither protocol raises
`NotContextManagerError`.

For example, use `initialize()` as an ASGI lifespan:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from yggdrasyl import deps


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with deps.initialize():
        yield


app = FastAPI(lifespan=lifespan)
```

## Scoped overrides

`Dependencies.scope()` creates a context-local registry layer. Registrations and
overrides made inside the scope are discarded when it exits.

```python
from yggdrasyl import Dependencies, from_instance

deps = Dependencies()
deps.register(int, from_instance(1))

with deps.scope():
    deps.register(int, from_instance(2), override=True)
    assert deps.resolve(int) == 2

assert deps.resolve(int) == 1
```

## Dependency wiring

Decorate a callable with `Dependencies.wire` and mark injectable parameters with
`Injected[Type]`. The container resolves marked parameters when they are omitted.

```python
from yggdrasyl import Dependencies, Injected, from_instance

deps = Dependencies()
deps.register(int, from_instance(2))


@deps.wire
def repeat(value: str, count: int = Injected[int]) -> str:
    return value * count


assert repeat("a") == "aa"
assert repeat("a", count=3) == "aaa"
```

Override injected parameters by keyword. Positional overrides for injectable parameters
are not supported.
