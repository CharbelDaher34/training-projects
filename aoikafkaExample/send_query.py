# streamlit_send_query.py
import streamlit as st
import asyncio
from aiokafka import AIOKafkaProducer

KAFKA_TOPIC = "queries"
KAFKA_SERVER = "localhost:9092"


async def send_query(query):
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_SERVER)
    await producer.start()
    try:
        await producer.send_and_wait(KAFKA_TOPIC, query.encode("utf-8"))
    finally:
        await producer.stop()


st.title("Query Input")
query = st.text_input("Enter your query:")

if st.button("Send Query") and query:
    asyncio.run(send_query(query))
    st.success("Query sent to Kafka!")
