# streamlit_display_response.py
import streamlit as st
import asyncio
from aiokafka import AIOKafkaConsumer

KAFKA_RESPONSE_TOPIC = "responses"
KAFKA_SERVER = "localhost:9092"


async def consume_responses():
    consumer = AIOKafkaConsumer(KAFKA_RESPONSE_TOPIC, bootstrap_servers=KAFKA_SERVER)
    await consumer.start()
    try:
        async for msg in consumer:
            st.write(msg.value.decode("utf-8"))
    finally:
        await consumer.stop()


st.title("LLM Responses")
st.write("Waiting for responses...")

if st.button("Start Listening"):
    asyncio.run(consume_responses())
