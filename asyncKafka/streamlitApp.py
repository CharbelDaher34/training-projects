import streamlit as st
from kafka import KafkaConsumer
import json
from datetime import datetime
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_minute_and_second(iso_time: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_time)
        minute_second = dt.strftime("%M:%S")
        return minute_second
    except ValueError:
        logger.error(f"Invalid time format received: {iso_time}")
        return "Invalid ISO time format. Please provide a valid ISO 8601 string."


# Initialize Kafka Consumer
logger.info("Initializing Kafka Consumer...")
try:
    consumer = KafkaConsumer(
        "inference-results",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="streamlit-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )
    logger.info("Kafka Consumer initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Kafka Consumer: {str(e)}")
    raise

st.title("LLM Inference Results")
st.write("Waiting for inference results...")

while True:
    try:
        for message in consumer:
            result = message.value
            logger.info(
                f"Received new inference result for query: {result['query'][:50]}..."
            )  # Log first 50 chars

            st.write(f"**Time:** {str(get_minute_and_second(result['time']))}")
            st.write(f"**Query:** {result['query']}")
            st.write(f"**Response:** {result['response']}")
            st.write("---")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
