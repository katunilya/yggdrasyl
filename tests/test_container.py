from typing import Callable

import pytest

from yggdrasyl import Container, Injected


@pytest.fixture
def container() -> Container:
    return Container()


class ServiceConfig: ...


class Service:
    def __init__(
        self,
        service_name: str,
        *,
        config: ServiceConfig = Injected,
    ) -> None:
        self._service_name = service_name
        self._url = config


def handler(_: int, *, service: Service = Injected) -> Service:
    return service


def wrong_handler(_: Service = Injected) -> None: ...


@pytest.fixture(autouse=True)
def register_url(container: Container) -> Container:
    container.register(ServiceConfig).as_instance(ServiceConfig())

    return container


@pytest.fixture
def wired_handler(container: Container) -> Callable:
    return container.wire(handler)


@pytest.fixture
def register_test_service_by_type_as_instance(container: Container) -> Container:
    container.register(Service).as_instance(Service(service_name="instance"))
    return container


@pytest.fixture
def register_test_service_by_type_as_factory(container: Container) -> Container:
    container.register(Service).as_factory(Service, service_name="factory")
    return container


@pytest.fixture
def register_test_service_by_type_as_cached_factory(container: Container) -> Container:
    container.register(Service).as_cached_factory(
        Service,
        service_name="cached-factory",
    )
    return container


def test_resolve_error(container: Container) -> None:
    with pytest.raises(KeyError) as err_info:
        container.resolve(Service)

    assert "dependency not found" in str(err_info)


@pytest.mark.usefixtures("register_test_service_by_type_as_instance")
def test_resolve_instance_by_type(container: Container) -> None:
    service = container.resolve(Service)
    assert service
    assert service._service_name == "instance"


@pytest.mark.usefixtures("register_test_service_by_type_as_factory")
def test_resolve_factory_by_type(container: Container) -> None:
    service_1 = container.resolve(Service)
    service_2 = container.resolve(Service)

    assert service_1
    assert service_2
    assert id(service_1) != id(service_2)
    assert service_1._service_name == "factory"
    assert service_2._service_name == "factory"


@pytest.mark.usefixtures("register_test_service_by_type_as_cached_factory")
def test_resolve_cached_factory_by_type(container: Container) -> None:
    service_1 = container.resolve(Service)
    service_2 = container.resolve(Service)

    assert service_1
    assert service_2
    assert id(service_1) == id(service_2)
    assert service_1._service_name == "cached-factory"


@pytest.mark.usefixtures("register_test_service_by_type_as_instance")
def test_wired_handler(wired_handler: Callable) -> None:
    wired_handler(1)


def test_wire_injected_argument_must_be_keyword_only(container: Container) -> None:
    with pytest.raises(Exception) as err_info:
        container.wire(wrong_handler)

    assert "must be kw only" in str(err_info)


@pytest.mark.usefixtures("register_test_service_by_type_as_instance")
def test_wire_injected_argument_replaced(
    container: Container, wired_handler: Callable
) -> None:
    service = Service(service_name="", config=ServiceConfig())

    returned_service = wired_handler(1, service=service)
    resolved_service = container.resolve(Service)

    assert resolved_service is not returned_service
    assert returned_service == service
