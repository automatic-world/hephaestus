from dependency_injector import containers, providers
from services.example_service import ExampleService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["routers"]
    )

    example_service = providers.Factory(ExampleService)
