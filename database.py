
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, select
from sqlalchemy.future import select
from datetime import datetime
import redis.asyncio as redis
import json

# Load environment variables from .env file
load_dotenv()

# --- PostgreSQL (Neon) Configuration ---
NEON_URI = os.getenv("NEON_URI")
if not NEON_URI:
    raise ValueError("NEON_URI environment variable not set")

engine = create_async_engine(NEON_URI.replace("postgresql://", "postgresql+psycopg://"), echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class Prediction(Base):
    """SQLAlchemy model for storing prediction records."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, index=True)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SensorReading(Base):
    """SQLAlchemy model for storing generic sensor readings."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    value = Column(String) # Using String for flexibility with different sensor types
    timestamp = Column(DateTime, default=datetime.utcnow)


async def init_db():
    """Initializes the database and creates tables."""
    async with engine.begin() as conn:
        # This will create the tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

# --- Redis Configuration ---
REDIS_USER_NAME = os.getenv("REDIS_USER_NAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CONNECTION_DETAILS = os.getenv("CONNECTION_DETAILS")

if not all([REDIS_USER_NAME, REDIS_PASSWORD, CONNECTION_DETAILS]):
    raise ValueError("Redis connection details (REDIS_USER_NAME, REDIS_PASSWORD, CONNECTION_DETAILS) are not fully set in environment variables")

redis_url = f"redis://{REDIS_USER_NAME}:{REDIS_PASSWORD}@{CONNECTION_DETAILS}"

redis_client = redis.from_url(redis_url, decode_responses=True)

# --- Data Persistence Logic ---
async def save_prediction(prediction_data: dict):
    """
    Saves a prediction to both PostgreSQL and Redis.
    """
    label = prediction_data.get("label")
    confidence = prediction_data.get("confidence")

    if label is None or confidence is None:
        print("Skipping save: prediction data is incomplete.")
        return

    # 1. Save to PostgreSQL for long-term storage
    async with AsyncSessionLocal() as session:
        async with session.begin():
            db_prediction = Prediction(
                label=label,
                confidence=float(confidence),
                timestamp=datetime.utcnow()
            )
            session.add(db_prediction)
        await session.commit()

    # 2. Save to Redis for short-term caching
    try:
        redis_payload = {
            "label": label,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        await redis_client.lpush("recent_predictions", json.dumps(redis_payload))
        await redis_client.ltrim("recent_predictions", 0, 99)
    except Exception as e:
        print(f"Error saving prediction to Redis: {e}")

async def save_sensor_data(sensor_data: dict):
    """
    Saves a generic sensor reading to both PostgreSQL and Redis.
    """
    sensor_id = sensor_data.get("sensor_id")
    value = sensor_data.get("value")

    if sensor_id is None or value is None:
        print("Skipping save: sensor data is incomplete.")
        return

    # 1. Save to PostgreSQL for long-term storage
    async with AsyncSessionLocal() as session:
        async with session.begin():
            db_reading = SensorReading(
                sensor_id=sensor_id,
                value=str(value), # Store value as string for flexibility
                timestamp=datetime.utcnow()
            )
            session.add(db_reading)
        await session.commit()

    # 2. Save to Redis for short-term caching
    try:
        redis_payload = {
            "sensor_id": sensor_id,
            "value": value,
            "timestamp": sensor_data.get("timestamp", datetime.utcnow().isoformat())
        }
        await redis_client.lpush("recent_sensor_data", json.dumps(redis_payload))
        await redis_client.ltrim("recent_sensor_data", 0, 99)
    except Exception as e:
        print(f"Error saving sensor data to Redis: {e}")

# --- Data Retrieval Logic ---

async def get_predictions(limit: int = 100):
    """Retrieve predictions from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Prediction).order_by(Prediction.timestamp.desc()).limit(limit)
        )
        return result.scalars().all()

async def get_recent_predictions(limit: int = 100):
    """Retrieve recent predictions from Redis."""
    try:
        predictions_json = await redis_client.lrange("recent_predictions", 0, limit - 1)
        return [json.loads(p) for p in predictions_json]
    except Exception as e:
        print(f"Error getting predictions from Redis: {e}")
        return []

async def get_sensor_readings(sensor_id: str = None, limit: int = 100):
    """Retrieve sensor readings from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        query = select(SensorReading).order_by(SensorReading.timestamp.desc())
        if sensor_id:
            query = query.filter(SensorReading.sensor_id == sensor_id)
        result = await session.execute(query.limit(limit))
        return result.scalars().all()

async def get_recent_sensor_readings(limit: int = 100):
    """Retrieve recent sensor readings from Redis."""
    try:
        readings_json = await redis_client.lrange("recent_sensor_data", 0, limit - 1)
        return [json.loads(r) for r in readings_json]
    except Exception as e:
        print(f"Error getting sensor readings from Redis: {e}")
        return []
