# fastapi_llm_backend.py
import asyncio
import logging
from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from transformers import pipeline
from datetime import datetime

# Initialize the FastAPI app
app = FastAPI()

# Kafka topics and server
KAFKA_QUERY_TOPIC = "queries"
KAFKA_RESPONSE_TOPIC = "responses"
KAFKA_SERVER = "localhost:9092"

# Initialize the model

llm = pipeline("text-generation", model="gpt2")  # Use a lightweight model for testing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def consume_queries():
    logger.info("Starting Kafka consumer and producer.")
    consumer = AIOKafkaConsumer(KAFKA_QUERY_TOPIC, bootstrap_servers=KAFKA_SERVER)
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_SERVER)
    await consumer.start()
    await producer.start()
    try:
        async for msg in consumer:
            query = msg.value.decode("utf-8")
            logger.info(f"Received query: {query}")

            # Generate response from the LLM
            try:
                response = llm(query, max_length=50)[0]["generated_text"]
                timestamp = datetime.now().isoformat()
                result = f"{timestamp} | Query: {query} | Response: {response}"
                logger.info(f"Generated response: {response}")

                # Send response back to Kafka
                await producer.send_and_wait(
                    KAFKA_RESPONSE_TOPIC, result.encode("utf-8")
                )
                logger.info(f"Sent response to topic '{KAFKA_RESPONSE_TOPIC}'")
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
    except Exception as e:
        logger.error(f"Error in Kafka consumer loop: {e}")
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Stopped Kafka consumer and producer.")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting backend service.")
    asyncio.create_task(consume_queries())
    logger.info("Kafka consumer task started.")
