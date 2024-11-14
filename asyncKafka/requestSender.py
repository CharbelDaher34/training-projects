import requests
import time


def send_requests():
    url = "http://localhost:8000/inference"
    prompts = [
        "What is the capital of France?",
        "Explain quantum mechanics.",
        "How does a car engine work?",
        "Tell me a joke.",
        "What is machine learning?",
    ]

    for prompt in prompts:
        response = requests.post(url, json={"prompt": prompt})
        print(f"Response for prompt '{prompt}': {response.json()}")
        time.sleep(0.5)  # Adjust the delay as needed


if __name__ == "__main__":
    send_requests()
