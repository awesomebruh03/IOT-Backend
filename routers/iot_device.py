from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dependencies import manager

router = APIRouter()

@router.websocket("/ws/data")
async def websocket_data_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process the received JSON data here
            await manager.broadcast_json(data, "data_room")
            await websocket.send_text(f"Received data: {data}")
    except WebSocketDisconnect:
        print("Client disconnected from data endpoint")

@router.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # Process the received audio data here
            await manager.broadcast_text("Received audio data", "ai_room")
            await websocket.send_text("Received audio data")
    except WebSocketDisconnect:
        print("Client disconnected from audio endpoint")
