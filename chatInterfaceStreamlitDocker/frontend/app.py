import streamlit as st
import requests

# Setup API endpoint variables
classificationUrl = "http://backend:8080/classify/"
feedbackUrl = "http://backend:8080/log-feedback/"


# Function to send query and get response
def send_query(query):
    try:
        response = requests.post(classificationUrl, json={"query": query})
        response.raise_for_status()
        return str(response.json().get("classification"))
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        return None


# Function to send feedback
def send_feedback(query, response, feedback):
    try:
        feedback_data = {"query": query, "response": response, "feedback": feedback}
        feedback_response = requests.post(feedbackUrl, json=feedback_data)
        feedback_response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error submitting feedback: {str(e)}")
        return False


# Main chat interface
st.title("Chat Interface with Feedback")

# Input textbox for user query
query = st.text_input("Enter your query:")

# Use session state to store the response and track if feedback has been submitted
if "response" not in st.session_state:
    st.session_state.response = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False

# Button to send query
if st.button("Send"):
    if query:
        st.session_state.response = send_query(query)
        st.session_state.feedback_submitted = False
    else:
        st.warning("Please enter a query first.")

# Display response and feedback options
if st.session_state.response:
    st.write("Response:", st.session_state.response)

    if not st.session_state.feedback_submitted:
        feedback = st.radio("Was this response helpful?", ["Good", "Bad"])
        if st.button("Submit Feedback"):
            print("\n\n\n\n\n\n\n\n\nSending feedback...\n\n\n\n\n\n\n\n\n\n\n")
            success = send_feedback(query, st.session_state.response, feedback)
            if success:
                st.success("Feedback submitted successfully")
                st.write(f"Your feedback: {feedback}")
                st.session_state.feedback_submitted = True
    else:
        st.info("Thank you for your feedback!")
