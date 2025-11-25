
from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from dependencies import manager
import inference
from database import get_predictions, get_recent_predictions, get_sensor_readings, get_recent_sensor_readings
from typing import List, Optional

router = APIRouter()

@router.post("/predict/")
async def predict_audio(file: UploadFile = File(...)):
    """
    Receives an audio file, preprocesses it, and returns a prediction.
    """
    try:
        # Read audio file content
        audio_bytes = await file.read()

        # Preprocess the audio and get MFCCs
        mfccs = inference.preprocess_audio(audio_bytes)

        # Get the prediction
        prediction = inference.predict(mfccs)

        # Return the prediction with a success status
        response_data = {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "status": "success"
        }
        
        # Broadcast the prediction to AI clients
        await manager.broadcast(f'{{"label": "{prediction["label"]}", "confidence": {prediction["confidence"]}}}', "ai_room")
        
        return JSONResponse(content=response_data)

    except Exception as e:
        # Return an error status if something goes wrong
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, status_code=500)

@router.get("/predictions/")
async def read_predictions(limit: int = 100):
    """
    Retrieve historical predictions from the database.
    """
    predictions = await get_predictions(limit=limit)
    return predictions

@router.get("/predictions/recent/")
async def read_recent_predictions(limit: int = 100):
    """
    Retrieve recent predictions from the cache.
    """
    predictions = await get_recent_predictions(limit=limit)
    return predictions

@router.get("/sensors/")
async def read_sensor_readings(sensor_id: Optional[str] = None, limit: int = 100):
    """
    Retrieve historical sensor readings from the database.
    """
    readings = await get_sensor_readings(sensor_id=sensor_id, limit=limit)
    return readings

@router.get("/sensors/recent/")
async def read_recent_sensor_readings(limit: int = 100):
    """
    Retrieve recent sensor readings from the cache.
    """
    readings = await get_recent_sensor_readings(limit=limit)
    return readings

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

