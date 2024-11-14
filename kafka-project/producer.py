# producer.py
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
from datetime import datetime
from pydantic import BaseModel
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class Notification(BaseModel):
    message: str
    priority: str


def create_kafka_producer():
    retries = 5
    while retries > 0:
        try:
            producer = KafkaProducer(
                bootstrap_servers=["kafka:9092"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=3,
            )
            logger.info("Successfully connected to Kafka!")
            return producer
        except KafkaError as e:
            logger.warning(
                f"Failed to connect to Kafka (retries left: {retries}): {str(e)}"
            )
            retries -= 1
            time.sleep(5)
    raise Exception("Failed to connect to Kafka after multiple attempts")


producer = create_kafka_producer()


@app.post("/send-notification/")
async def send_notification(notification: Notification):
    try:
        # Ensure priority is either "high" or "normal"
        priority = notification.priority.lower()
        # if priority not in ["high", "normal"]:
        #     priority = "normal"

        notification_data = {
            "message": notification.message,
            "priority": priority,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info(f"Sending notification: {notification_data}")
        future = producer.send("notifications", notification_data)
        result = future.get(timeout=10)
        producer.flush()

        logger.info(
            f"Notification sent successfully to partition {result.partition} at offset {result.offset}"
        )
        return {
            "status": "success",
            "message": "Notification sent successfully",
            "notification": notification_data,
        }
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    try:
        producer.bootstrap_connected()
        return {"status": "healthy", "kafka_connected": True}
    except Exception as e:
        return {"status": "unhealthy", "kafka_connected": False, "error": str(e)}
