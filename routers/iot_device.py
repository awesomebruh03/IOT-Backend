from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dependencies import manager
from database import save_prediction, save_sensor_data, AsyncSessionLocal
import inference
import json
import asyncio

router = APIRouter()

async def session_commit_task(session):
    """Periodically commits the session to keep the connection alive."""
    while True:
        await asyncio.sleep(60) # Commit every 60 seconds
        await session.commit()

@router.websocket("/ws/data")
async def websocket_data_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("IoT device connected to data endpoint")
    async with AsyncSessionLocal() as session:
        commit_task = asyncio.create_task(session_commit_task(session))
        try:
            while True:
                data = await websocket.receive_json()
                
                # Save sensor data using the existing session
                await save_sensor_data(data, session)
                
                # Broadcast data to clients
                await manager.broadcast_json(data, "data_room")
                
                # Send confirmation back to device
                await websocket.send_text(f"Received data: {data}")

        except WebSocketDisconnect:
            print("Client disconnected from data endpoint")
        except Exception as e:
            print(f"Error in data endpoint: {e}")
        finally:
            commit_task.cancel()
            await session.commit() # Final commit before closing

@router.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("IoT device connected to audio endpoint")
    async with AsyncSessionLocal() as session:
        commit_task = asyncio.create_task(session_commit_task(session))
        try:
            while True:
                audio_bytes = await websocket.receive_bytes()

                # 1. Preprocess audio
                mfccs = inference.preprocess_audio(audio_bytes)

                # 2. Get prediction
                prediction = inference.predict(mfccs)

                # 3. Create response data payload
                response_data = {
                    "label": prediction["label"],
                    "confidence": prediction["confidence"]
                }
                
                # 4. Save prediction using the existing session
                await save_prediction(response_data, session)

                # 5. Broadcast prediction to client app
                await manager.broadcast(json.dumps(response_data), "ai_room")

                # 6. Send confirmation to IoT device
                await websocket.send_text(f"Processed audio. Prediction: {prediction['label']}")

        except WebSocketDisconnect:
            print("IoT device disconnected from audio endpoint")
        except Exception as e:
            print(f"Error in audio endpoint: {e}")
        finally:
            commit_task.cancel()
            await session.commit() # Final commit before closing
