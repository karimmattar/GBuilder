"""
2 ways websocket path implementation:
    1. WebSocketEndpoint with list of routes (preferred).
        ```
        from starlette.endpoints import WebSocketEndpoint
        from starlette.routing import WebSocketRoute
        
        class Echo(WebSocketEndpoint):
            async def on_receive(self, websocket, data):
                await websocket.send_text(f"Message text was: {data}")
        
        routes = [
            WebSocketRoute("/", Echo),
        ]
        
        app = GBuilder(routes=routes)
        ---------------------------------------------
        app.run(host="127.0.0.1", port=8000)
        # Uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)
        # Uvicorn in terminal
        uvicorn main:app --host 127.0.0.1 --port 8000
        ```
    2. route & websocket_route decorators.
        ```
        from starlette.websockets import WebSocket
        
        app = GBuilder()
        
        @app.websocket_route("/") # or you can use '@app.route("/")' instead.
        async def websocket_handler(websocket: WebSocket):
            await websocket.accept()
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Message text was: {data}")
        --------------------------------------------------------------
        app.run(host="127.0.0.1", port=8000)
        # Uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)
        # Uvicorn in terminal
        uvicorn main:app --host 127.0.0.1 --port 8000
        ```
"""

from starlette.websockets import WebSocket
from gbuilder.applications import GBuilder

app = GBuilder()


@app.route("/")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
