from fastapi import FastAPI
from routers import iot_device, client, simulation
from database import init_db

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Event handler for application startup."""
    print("Application starting up...")
    await init_db()
    print("Database initialized.")

app.include_router(iot_device.router, prefix="/iot", tags=["IoT Device"])
app.include_router(client.router, prefix="/client", tags=["Client App"])
app.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])

@app.get("/")
async def root():
    return {"message": "Server is running"}

