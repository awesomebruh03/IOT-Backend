
import asyncio
import json
import random
import os
from fastapi import APIRouter, BackgroundTasks
from dependencies import manager
from datetime import datetime, timezone
import inference
import kagglehub

router = APIRouter(tags=["simulation"])

# In-memory state to control the simulation
simulation_running = False

async def run_audio_simulation():
    """
    A background task that simulates audio data, processes it, and broadcasts predictions.
    """
    global simulation_running
    if simulation_running:
        print("Audio simulation is already running.")
        return

    print("Starting audio simulation...")
    simulation_running = True

    # 1. Download the dataset
    print("Downloading dataset...")
    try:
        path = kagglehub.dataset_download("mmoreaux/environmental-sound-classification-50")
        audio_dir = os.path.join(path, "audio/audio")
        # Get a list of all audio files
        audio_files = [os.path.join(root, file)
                       for root, _, files in os.walk(audio_dir)
                       for file in files if file.endswith((".wav", ".flac", ".mp3"))]
        print(f"Dataset downloaded. Found {len(audio_files)} audio files.")
    except Exception as e:
        print(f"Error downloading or processing dataset: {e}")
        simulation_running = False
        return

    while simulation_running:
        try:
            # 2. Pick a random audio file
            random_audio_file = random.choice(audio_files)
            print(f"Simulating with: {random_audio_file}")

            with open(random_audio_file, "rb") as f:
                audio_bytes = f.read()

            # 3. Preprocess and predict (reusing existing logic)
            mfccs = inference.preprocess_audio(audio_bytes)
            prediction = inference.predict(mfccs)

            # 4. Format the response
            response_data = {
                "label": prediction["label"],
                "confidence": prediction["confidence"]
            }

            # 5. Broadcast
            await manager.broadcast_text(json.dumps(response_data), "ai_room")
            
            # 6. Wait for a bit before the next simulation
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error during simulation loop: {e}")
            await asyncio.sleep(10) # Wait longer if there's an error

    print("Audio simulation stopped.")

async def run_sensor_simulation():
    """
    A background task that simulates various sensor data and broadcasts it.
    """
    global simulation_running
    print("Starting sensor data simulation...")

    while simulation_running:
        try:
            # Simulate data for each sensor type
            sensor_simulations = [
                {"sensor_id": "dht11-temp", "value": random.uniform(20.0, 30.0)},
                {"sensor_id": "dht11-humidity", "value": random.uniform(40.0, 60.0)},
                {"sensor_id": "ultrasonic", "value": random.uniform(10, 300)},
                {"sensor_id": "mq2", "value": random.uniform(100, 1000)},
                {"sensor_id": "ir-flame", "value": float(random.choice([0, 1]))} # value as float
            ]

            for sim in sensor_simulations:
                if not simulation_running:
                    break
                
                sensor_data = {
                    "sensor_id": sim["sensor_id"],
                    "value": f'{sim["value"]:.2f}',
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await manager.broadcast_json(sensor_data, "data_room") 
                print(f"Simulated and sent data: {sensor_data}")

                # Short delay between sending each sensor's data
                await asyncio.sleep(1)

            # Wait for a longer period before the next batch of simulations
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error during sensor simulation loop: {e}")
            await asyncio.sleep(10)

    print("Sensor data simulation stopped.")


@router.post("/trigger")
async def trigger_simulation(payload: dict, background_tasks: BackgroundTasks):
    """
    Starts or stops the audio and sensor data simulation.
    Expects a JSON payload with an "action" key ("start" or "stop").
    """
    global simulation_running
    action = payload.get("action")

    if action == "start":
        if simulation_running:
            return {"status": "error", "message": "Simulation is already running."}
        # Starts both audio and sensor simulation in the background
        background_tasks.add_task(run_audio_simulation)
        background_tasks.add_task(run_sensor_simulation)
        return {"status": "success", "message": "Audio and sensor simulation started."}
    
    elif action == "stop":
        if not simulation_running:
            return {"status": "error", "message": "Simulation is not running."}
        simulation_running = False
        return {"status": "success", "message": "Audio and sensor simulation stopped."}
        
    else:
        return {"status": "error", "message": "Invalid action. Use 'start' or 'stop'."}
