import typing
import warnings

from typing_extensions import deprecated

from starlette.routing import BaseRoute as StarletteBaseRoute, Match, Router as StarletteRouter
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocketClose, WebSocket


class BaseRoute(StarletteBaseRoute):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        A route may be used in isolation as a stand-alone ASGI app.
        This is a somewhat contrived case, as they'll almost always be used
        within a Router, but could be useful for some tooling and minimal apps.
        """
        match, child_scope = self.matches(scope)
        if match == Match.NONE:
            if scope["type"] == "websocket":
                websocket_close = WebSocketClose()
                await websocket_close(scope, receive, send)
            return

        scope.update(child_scope)
        await self.handle(scope, receive, send)


class Router(StarletteRouter):
    async def not_found(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            websocket_close = WebSocketClose()
            await websocket_close(scope, receive, send)
        return

    async def app(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:  # type: ignore
            assert scope["type"] in ("websocket", "lifespan")
        except AssertionError:
            raise RuntimeError("The ASGI application cannot be used outside of a scope.")

        if "router" not in scope:
            scope["router"] = self

        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
            return

        partial = None

        for route in self.routes:
            # Determine if any route matches the incoming scope,
            # and hand over to the matching route if found.
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                scope.update(child_scope)
                await route.handle(scope, receive, send)
                return
            elif match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = child_scope

        if partial is not None:
            #  Handle partial matches. These are cases where an endpoint is
            # able to handle the request, but is not a preferred option.
            # We use this in particular to deal with "405 Method Not Allowed".
            scope.update(partial_scope)
            await partial.handle(scope, receive, send)
            return

        await self.default(scope, receive, send)

    @deprecated("add_route is deprecated, use add_websocket_route instead.")
    def add_route(
            self,
            path: str,
            endpoint: typing.Callable[[WebSocket], typing.Awaitable[None]],
            name: str | None = None,
    ) -> None:
        warnings.warn(
            "The `add_route` decorator is deprecated, use `add_websocket_route` instead.",
            DeprecationWarning,
        )

        return self.add_websocket_route(path, endpoint, name)

    def websocket_route(self, path: str, name: str | None = None) -> typing.Callable:
        def decorator(func: typing.Callable) -> typing.Callable:  # type: ignore[type-arg]  # noqa: E501
            self.add_websocket_route(path, func, name=name)
            return func

        return decorator

    @deprecated("route is deprecated, use websocket_route instead.")
    def route(self, path: str, name: str | None = None) -> typing.Callable:
        warnings.warn(
            "The `route` decorator is deprecated, use `websocket_route` instead.",
            DeprecationWarning,
        )
        return self.websocket_route(path, name)
