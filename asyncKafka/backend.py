from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import time

app = FastAPI()

producer = None
for _ in range(5):  # Retry 5 times
    try:
        producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        break
    except Exception as e:
        print("Kafka not available, retrying in 5 seconds...")
        time.sleep(5)

if producer is None:
    raise Exception("Kafka Producer could not connect after retries.")


class InferenceRequest(BaseModel):
    prompt: str


@app.post("/inference")
async def inference(request: InferenceRequest):
    try:
        # Send request to Kafka topic
        producer.send("inference-requests", request.dict())
        return {"message": "Request queued for processing."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=8000)
