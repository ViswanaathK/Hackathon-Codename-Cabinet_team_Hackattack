import streamlit as st
import requests
from string import punctuation

#API to call the genai endpoint deployed in AWS
CUSTOM_API_URL = "https://977r0izqz2.execute-api.us-east-1.amazonaws.com/dev/Chat_bot_Invoice_Rejection"

def remove_punctuation(input_string):
    '''
    To remove all punctuation in a given string
    '''
    return ''.join(char for char in input_string if char not in punctuation)

def endpoint_caller(question):
    '''
    The function to call the API
    '''
    payload = f"""{{
        "question": "{question}"
    }}"""
    headers = {
    'Content-Type': 'text/plain'
    }

    response = requests.request("GET", CUSTOM_API_URL, headers=headers, data=payload)

    print(response.text)
    return response

# Custom CSS to center the title
st.markdown("<h1 style='text-align: center; color: white;'>SCF Chatbot</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input from the user
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the custom API
    response = endpoint_caller(prompt)

    if response.status_code == 200:
        assistant_response = response.json()
    else:
        assistant_response = "Error: Unable to get response from API."

    for ind,asst_response in assistant_response.items():
        if len(remove_punctuation(asst_response)):
            # Display the assistant's response
            st.session_state.messages.append({"role": "assistant", "content": asst_response})
            with st.chat_message("assistant"):
                st.markdown(asst_response)
