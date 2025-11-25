from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("connection on")
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
