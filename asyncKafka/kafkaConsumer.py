from kafka import KafkaConsumer, KafkaProducer
import json
from transformers import pipeline
from datetime import datetime
import logging
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("kafka_inference.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting the Kafka inference service")

try:
    # Load a small model from Hugging Face
    logger.info("Loading distilgpt2 model...")
    llm = pipeline(
        "text-generation", model="distilgpt2", pad_token_id=0)
    logger.info("Model loaded successfully")

    # Initialize Kafka Consumer
    logger.info("Initializing Kafka Consumer...")
    consumer = KafkaConsumer(
        "inference-requests",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="my-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )
    logger.info("Kafka Consumer initialized successfully")

    # Initialize Kafka Producer
    logger.info("Initializing Kafka Producer...")
    producer = KafkaProducer(
        bootstrap_servers="kafka:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    logger.info("Kafka Producer initialized successfully")

except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

# Main processing loop
logger.info("Starting main processing loop")
for message in consumer:
    logger.info(
        f"Received message from topic {message.topic} partition {message.partition} offset {message.offset}"
    )

    request = message.value
    logger.debug(f"Processing request: {request}")

    try:
        # Process the request using the LLM
        logger.info(
            f"Generating text for prompt: {request['prompt'][:100]}..."
        )  # Log first 100 chars of prompt
        result = llm(request["prompt"])
        logger.debug(f"Raw model output: {result}")

        # Prepare the message with time, query, and response
        response_message = {
            "time": datetime.now().isoformat(),
            "query": request["prompt"],
            "response": result[0]["generated_text"],
        }

        logger.info("Text generation completed successfully")
        logger.debug(f"Prepared response message: {response_message}")

        # Send the result back to Kafka
        logger.info("Sending response to 'inference-results' topic...")
        future = producer.send("inference-results", response_message)
        future.get(timeout=10)  # Wait for the message to be sent
        logger.info("Response sent successfully")

    except Exception as e:
        logger.error(f"Error processing request: {request}")
        logger.exception(e)  # This logs the full stack trace

    finally:
        # Ensure messages are sent
        producer.flush()

# Cleanup
logger.info("Shutting down Kafka inference service")
try:
    producer.close()
    consumer.close()
    logger.info("Kafka connections closed successfully")
except Exception as e:
    logger.error(f"Error during cleanup: {str(e)}")
