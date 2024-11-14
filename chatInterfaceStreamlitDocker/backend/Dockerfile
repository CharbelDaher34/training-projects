FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN pip install torch  --index-url https://download.pytorch.org/whl/cpu

# Pre-download the Hugging Face model and tokenizer using the pipeline
RUN python -c "from transformers import pipeline; \
               pipeline(model='lxyuan/distilbert-base-multilingual-cased-sentiments-student')"
COPY . .

EXPOSE 8080

# CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]
# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--host", "0.0.0.0", "--port", "8080"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
