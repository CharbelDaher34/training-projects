from kafka import KafkaConsumer
import json
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProcessingStats:
    def __init__(self):
        self.total_messages = 0
        self.total_time = 0
        self.start_time = time.time()

    def update(self, processing_time):
        self.total_messages += 1
        self.total_time += processing_time

    def get_stats(self):
        elapsed_time = time.time() - self.start_time
        avg_processing_time = (
            self.total_time / self.total_messages if self.total_messages > 0 else 0
        )
        messages_per_second = (
            self.total_messages / elapsed_time if elapsed_time > 0 else 0
        )

        return {
            "total_messages": self.total_messages,
            "avg_processing_time_ms": round(avg_processing_time * 1000, 2),
            "messages_per_second": round(messages_per_second, 2),
            "total_runtime_seconds": round(elapsed_time, 2),
        }


def main():
    # Create stats tracker
    stats = ProcessingStats()

    # Create Kafka consumer
    consumer = KafkaConsumer(
        "processed_data",
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="latest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        key_deserializer=lambda x: x.decode("utf-8") if x else None,
    )

    logger.info("Starting consumer... waiting for messages")

    try:
        for message in consumer:
            # Record processing start time
            start_time = time.time()

            # Parse and process message
            data = message.value

            # Calculate processing time
            processing_time = time.time() - start_time
            stats.update(processing_time)

            # Log every 100 messages
            if stats.total_messages % 100 == 0:
                current_stats = stats.get_stats()
                logger.info("\nProcessing Statistics:")
                logger.info(
                    f"Total Messages Processed: {current_stats['total_messages']}"
                )
                logger.info(
                    f"Average Processing Time: {current_stats['avg_processing_time_ms']} ms"
                )
                logger.info(
                    f"Messages per Second: {current_stats['messages_per_second']}"
                )
                logger.info(
                    f"Total Runtime: {current_stats['total_runtime_seconds']} seconds"
                )
                logger.info("=" * 50)

    except KeyboardInterrupt:
        logger.info("\nShutting down consumer...")
    finally:
        consumer.close()
        logger.info("Consumer closed")


if __name__ == "__main__":
    main()
