from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dependencies import manager

router = APIRouter()

@router.websocket("/ws/client/data")
async def websocket_client_data_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "data_room")
    try:
        while True:
            # Keep the connection open to send data to the client
            await websocket.receive_text() # We need to keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "data_room")
        print("Client disconnected from client data endpoint")

@router.websocket("/ws/client/ai")
async def websocket_client_ai_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "ai_room")
    try:
        while True:
            # Keep the connection open to send data to the client
            await websocket.receive_text() # We need to keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "ai_room")
        print("Client disconnected from client AI endpoint")
