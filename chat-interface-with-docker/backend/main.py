## Input
### Import necessary libraries
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

### Setup FastAPI app and load Hugging Face model
app = FastAPI()
pipe = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct")


### Define request body structure
class QueryRequest(BaseModel):
    query: str


## Model
### Define an endpoint that takes a query, applies it to the model, and returns the result
@app.post("/chat")
def apply_model(request: QueryRequest):

    messages = [
        {"role": "user", "content": request.query},
    ]
    result = pipe(messages, max_new_tokens=50)
    # Extracting only the assistant's content
    assistant_response = result[0]["generated_text"][1][
        "content"
    ]  # Assuming assistant's content is at index 1
    return {"result": assistant_response}


## Output
### Start FastAPI server (run this command in terminal, not within the script)
# uvicorn script_name:app --reload
