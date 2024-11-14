FROM python:3.10-slim

WORKDIR /app


# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the frontend files
COPY . .

EXPOSE 8501

# Command to run the frontend app
CMD ["streamlit" ,"run" ,"app.py"]
