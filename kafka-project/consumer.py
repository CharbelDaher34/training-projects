import streamlit as st
import time
from kafka import KafkaConsumer
import json


# Function to read messages from Kafka
def get_kafka_messages(topic):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers="kafka:9092",  # Change this if your Kafka server is different
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        # group_id="notification_group",
    )
    return consumer


# Streamlit app
st.title("Kafka Notifications")

# Initialize an empty list to store messages
messages = []

# Create a Kafka consumer
consumer = get_kafka_messages("notifications")

# Display messages every 5 seconds
# Read a message from Kafka
for message in consumer:
    messages.append(message.value)  # Append the message to the list
    st.write(message.value)  # Display the message on the Streamlit app
# time.sleep(5)  # Wait for 5 seconds before reading again
