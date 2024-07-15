import typing

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.websockets import WebSocket
from .datastructure import State, URLPath
from .routing import BaseRoute, Router
from .types import ExceptionHandler, ASGIApp, Lifespan

AppType = typing.TypeVar("AppType", bound="GBuilder")


class GBuilder(Starlette):
    def __init__(
            self: AppType,
            debug: bool = False,
            routes: typing.Sequence[BaseRoute] | None = None,
            on_connect: typing.Sequence[Middleware] | None = None,
            exception_handlers: typing.Mapping[typing.Any, ExceptionHandler] | None = None,
            on_startup: typing.Sequence[typing.Callable[[], typing.Any]] | None = None,
            on_shutdown: typing.Sequence[typing.Callable[[], typing.Any]] | None = None,
            lifespan: Lifespan[AppType] | None = None,
    ) -> None:
        super().__init__(debug, routes, on_connect, exception_handlers, on_startup, on_shutdown, lifespan)
        assert lifespan is None or (
                on_startup is None and on_shutdown is None
        ), "Use either 'lifespan' or 'on_startup'/'on_shutdown', not both."

        self.debug = debug
        self.state = State()
        self.router = Router(
            routes, on_startup=on_startup, on_shutdown=on_shutdown, lifespan=lifespan
        )
        self.exception_handlers = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self.user_middleware = [] if on_connect is None else list(on_connect)
        self.middleware_stack: ASGIApp | None = None

    def url_path_for(self, name: str, /, **path_params: typing.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    def add_websocket_route(
            self,
            path: str,
            route: typing.Callable[[WebSocket], typing.Awaitable[None]],
            name: str | None = None,
    ) -> None:  # pragma: no cover
        self.router.add_websocket_route(path, route, name=name)

    def websocket_route(self, path: str, name: str | None = None) -> typing.Callable:  # type: ignore[type-arg]

        def decorator(func: typing.Callable) -> typing.Callable:  # type: ignore[type-arg]  # noqa: E501
            self.router.add_websocket_route(path, func, name=name)
            return func

        return decorator

    def add_route(
            self,
            path: str,
            route: typing.Callable[[WebSocket], typing.Awaitable[None]],
            name: str | None = None,
    ) -> None:
        return self.add_websocket_route(path, route, name=name)

    def route(self, path: str, name: str | None = None) -> typing.Callable:
        return self.websocket_route(path, name=name)
