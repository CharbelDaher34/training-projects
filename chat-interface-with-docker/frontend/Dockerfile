FROM python:3.10-slim

WORKDIR /app

# Install tkinter
# RUN apt-get install -y python3-tk
RUN apk update && apk add --no-cache tcl tk xvfb-run

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the frontend files
COPY . .

EXPOSE 80

# Command to run the frontend app
CMD ["xvfb-run", "python", "app.py"]
