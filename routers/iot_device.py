from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dependencies import manager
from database import save_prediction, save_sensor_data
import inference
import json

router = APIRouter()

@router.websocket("/ws/data")
async def websocket_data_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("IoT device connected to data endpoint")
    try:
        while True:
            data = await websocket.receive_json()
            
            # Save the sensor data to the databases
            await save_sensor_data(data)
            
            # Broadcast the data to clients
            await manager.broadcast_json(data, "data_room")
            
            # Send confirmation back to device
            await websocket.send_text(f"Received data: {data}")

    except WebSocketDisconnect:
        print("Client disconnected from data endpoint")
    except Exception as e:
        print(f"Error in data endpoint: {e}")


@router.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("IoT device connected to audio endpoint")
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()

            # 1. Preprocess the audio to get MFCCs
            mfccs = inference.preprocess_audio(audio_bytes)

            # 2. Get the prediction
            prediction = inference.predict(mfccs)

            # 3. Create the response data payload
            response_data = {
                "label": prediction["label"],
                "confidence": prediction["confidence"]
            }
            
            # 4. Save the prediction to the databases
            await save_prediction(response_data)

            # 5. Broadcast the prediction to the client app (ai_room)
            await manager.broadcast(json.dumps(response_data), "ai_room")

            # 6. Send a confirmation back to the IoT device (optional)
            await websocket.send_text(f"Received and processed audio. Prediction: {prediction['label']}")

    except WebSocketDisconnect:
        print("IoT device disconnected from audio endpoint")
    except Exception as e:
        # You might want to log the error more formally
        print(f"Error in audio endpoint: {e}")
