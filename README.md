# yggsdrasyl

Simplistic, but totally explicit dependency injection tool. Main goal is to provide
simple, but powerful API for registering dependencies by type and their extensible
resolution mechanism in functions.

> Why `yggdrasyl`? This is misspelling of `yggdrasil` - the ancient tree of life in
> Nordic / Scandinavian mythologies, that connects all the worlds, like DI Framework
> connects dependencies.

## Usage

Main entry point to dependency management is class `Dependencies`. You can create your
own instance, or use predefined global one - `deps`.

### Dependency Registration

To register a dependency invoke method `Dependencies.register`:

```python
from yggdrasyl import deps


deps.register(UserServiceConfig, lambda d: UserServiceConfig())
deps.register(UserService, lambda d: UserService(config=d.resolve(UserServiceConfig)))
```

`Dependencies.register` accepts accepts 2 required arguments:

1. dependency type - identifier for dependency resolution
2. factory function - function that accepts `Dependencies` object and returns dependency
   instance

Also there are multiple optional keyword-only arguments:

1. `cached` - if `True` than dependency object is reused across all resolutions, `True`
   by default
2. `managed` - if `True` than dependency object is managed by context manager and can be
   initialized with all the other dependencies
3. `override` - if `True` than existing dependency with same type is overridden, `False`
   by default

For simplification of registering objects from instances one case use `from_instance`
utility function. If one has factory function (for example class constructor) use
`from_factory`.

```python
from yggdrasyl import deps


deps.register(int, from_instance(1))
deps.register(IService, from_factory(Service))
```

If dependency type is already registered, then `TypeAlreadyRegisteredError` is raised.

### Dependency Resolution

To resolve dependency invoke `Dependencies.resolve` method with single desired type
argument:

```python
from yggdrasyl import deps

user_service = deps.resolve(UserService)
```

If type is not registered, then `TypeNotRegisteredError` is raised.

### Context Manager Dependencies

Some dependencies require being initialized on application startup. In order not to
forget one and rule management from single place there is a `managed` parameter, that
indicates that this dependency should be resolved on startup and is sync or async
context manager, that should be initialized.

After marking only dependencies as `managed` just open `Dependencies.initialize` context
and all the dependencies will be initialized at once. Basically this method should be
used as lifespan for ASGI applications (for example).

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from yggdrasyl import deps


@asynccontextmanager
async def _lifespan(app: FastAPI):
    async with deps.initialize():
        yield
```

### Dependency Wiring

In order not to call `Dependencies.resolve` manually for each dependency, there is a way to tell that some callable requires some dependencies via `Dependencies.wire` decorator:

```python
from yggdrasyl import deps, Injected


@deps.wire
async def _handle_register_user(
    action: RegisterUser,
    user_service: UserService = Injected[UserService]
) -> UserID:
    ...
```

To mark argument to be injected from DI container one should use `Injected` object with
wanted type in `[]`.
