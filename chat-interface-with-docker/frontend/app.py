## Input
### Import necessary libraries
import tkinter as tk
import requests

### Setup variables
backend_url = "http://backend:8000/chat"  # Change if the backend URL is different


## Model
### Define function to send message to backend and display response
def send_message():
    user_message = entry.get()  # Get user message from input
    if not user_message:
        return

    # Send the message to the backend
    response = requests.post(backend_url, json={"query": user_message})

    # Display user message in chat box
    chat_box.insert(tk.END, f"User: {user_message}\n")

    # Clear the input field
    entry.delete(0, tk.END)

    # Display the response from the backend
    if response.status_code == 200:
        result = response.json().get("result", "No result")
        chat_box.insert(tk.END, f"Bot: {result}\n")
    else:
        chat_box.insert(tk.END, "Error: Could not retrieve response from backend.\n")


## Output
### Setup basic frontend using Tkinter
root = tk.Tk()
root.title("Chat Interface")

# Chat box where messages are displayed
chat_box = tk.Text(root, height=20, width=50)
chat_box.pack()

# Entry box where user types the message
entry = tk.Entry(root, width=50)
entry.pack()

# Send button
send_button = tk.Button(root, text="Send", command=send_message)
send_button.pack()

# Start the Tkinter main loop
root.mainloop()
