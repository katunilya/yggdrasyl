from typing import Type


class TypeAlreadyRegisteredError(Exception):
    def __init__(self, type_: Type) -> None:
        self.type = type_

        super().__init__(f"{type_.__name__} already registered")


class TypeNotRegisteredError(Exception):
    def __init__(self, type_: Type) -> None:
        self.type = type_

        super().__init__(f"{type_.__name__} not registered")


class TypeResolutionError(Exception):
    def __init__(self, type_: Type) -> None:
        self.type = type_

        super().__init__(f"{type_.__name__} failed to be resolved")


class NotContextManagerError(Exception):
    def __init__(self, dependency: object) -> None:
        self.dependency = dependency

        super().__init__(f"{dependency} is not a context manager")
