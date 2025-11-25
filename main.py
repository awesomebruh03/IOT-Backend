from fastapi import FastAPI
from routers import iot_device, client

app = FastAPI()

app.include_router(iot_device.router)
app.include_router(client.router)
