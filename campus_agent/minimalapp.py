"""
minimalapp.py - Starting point for Lab 3

This is a basic Streamlit chat interface without ADK integration.
Students will modify this file to add agent connectivity.

Author: [Student Name]
Course: AI Programming
"""

import streamlit as st

# Page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Campus Resource Assistant",
    page_icon="🏛️",
    layout="centered"
)

# Title and introduction
st.title("🏛️ Campus Resource Assistant")

st.markdown("""
Ask me about campus resources like the library, tutoring center, 
advising office, or financial aid. I can help you find hours, 
locations, and contact information.
""")

# Initialize chat history in session state
# This persists across Streamlit's reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display all messages from chat history
# Each message is a dict with 'role' and 'content' keys
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input using walrus operator for assignment + condition check
if prompt := st.chat_input("Ask about campus resources..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message immediately (Streamlit doesn't auto-show input)
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Placeholder response - will be replaced with real agent call
    with st.chat_message("assistant"):
        response = f"You asked: '{prompt}'. Agent connection coming in next steps."
        st.markdown(response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Clear conversation button
if st.button("Clear Conversation"):
    st.session_state.messages = []
    st.rerun()
