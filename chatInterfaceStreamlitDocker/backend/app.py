from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import pipeline
import json
from pathlib import Path
from fastapi.logger import logger
import logging
from fastapi.responses import JSONResponse


# Configure file logging
file_handler = logging.FileHandler("api.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Configure console logging (terminal output)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_formatter)

# Add both handlers to the FastAPI logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set logger level
logger.setLevel(logging.INFO)

pipe = pipeline(
    model="lxyuan/distilbert-base-multilingual-cased-sentiments-student", top_k=None
)


class QueryRequest(BaseModel):
    query: str


class FeedbackRequest(BaseModel):
    query: str
    response: str
    feedback: str


app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request details
    logger.info(f"Received {request.method} request at {request.url}")

    # Read request body
    request_body = await request.body()

    # Call the next middleware or route handler
    try:
        response = await call_next(request)

        # Check response status code
        if response.status_code == 200:
            logger.info(
                f"Returned response with status code {response.status_code}\n\n\n"
            )
        else:
            # Read response content by using a custom response object
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Rebuild the response (since we've read the body)
            response = JSONResponse(
                content=json.loads(response_body.decode()),
                status_code=response.status_code,
            )

            # Log full details in case of non-200 response
            logger.error(
                f"Returned response with status code {response.status_code}, "
                f"Method: {request.method}, "
                f"Request URL: {request.url}, "
                f"Request Body: {request_body.decode('utf-8') if request_body else 'None'}, "
                f"Response Content: {response_body.decode('utf-8')}\n\n\n"
            )
    except Exception as e:
        logger.error(f"Exception occurred during request handling: {str(e)}\n\n\n")
        raise

    return response


@app.head("/classify/")
@app.post("/classify/")
async def classify_language(request: QueryRequest):
    try:
        logger.info(f"Processing classification request for query: {request.query}")
        result = pipe(request.query)
        logger.info(f"Classification result: {result}")
        return {"classification": result}
    except Exception as e:
        logger.error(f"Error in classification: {str(e)}")
        raise


log_file_path = Path("feedback_log.json")


def log_feedback(data):
    try:
        if log_file_path.exists():
            with open(log_file_path, "r") as file:
                log_data = json.load(file)
        else:
            log_data = []
        log_data.append(data)
        with open(log_file_path, "w") as file:
            json.dump(log_data, file, indent=4)
        logger.info(f"Feedback logged to {log_file_path}")
    except Exception as e:
        logger.error(f"Error logging feedback: {str(e)}")
        raise


@app.post("/log-feedback/")
async def log_feedback_endpoint(request: FeedbackRequest):
    try:
        feedback_data = {
            "query": request.query,
            "response": request.response,
            "feedback": request.feedback,
        }

        logger.info(f"Logging feedback: {feedback_data}")
        log_feedback(feedback_data)
        return {"message": "Feedback logged successfully", "data": feedback_data}
    except Exception as e:
        logger.error(f"Error in log_feedback_endpoint: {str(e)}")
        raise
