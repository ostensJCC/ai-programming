"""
app.py - Final version for Lab 3

Complete Streamlit chat interface with ADK agent integration.
This file connects to the Campus Resource Assistant agent from Lab 2.

Author: [Student Name]
Course: AI Programming
"""

import streamlit as st
import asyncio
import os
import sys
from pathlib import Path

# --- Page Configuration (MUST be first Streamlit command) ---
st.set_page_config(
    page_title="Campus Resource Assistant",
    page_icon="🏛️",
    layout="centered"
)

# --- Environment and API Key Handling (MUST happen before ADK imports) ---

# Add the current directory to Python path so we can import agent.py
sys.path.insert(0, str(Path(__file__).parent))

# Load API key from .env file (local development)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Verify API key is available before proceeding
if "GOOGLE_API_KEY" not in os.environ or not os.environ["GOOGLE_API_KEY"]:
    st.error("""
    **API Key Not Found**
    
    Create a `.env` file in the campus_agent folder with:
    ```
    GOOGLE_API_KEY=your-key-here
    ```
    
    For Streamlit Cloud deployment, see Part VII of the lab
    for instructions on configuring secrets.
    """)
    st.stop()

# --- ADK Imports (after API key is set) ---
# Using canonical import paths per ADK documentation
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

# Import our agent from Lab 2
from agent import root_agent, RESOURCE_FILE

# --- Constants for ADK Session Management ---

APP_NAME = "campus_resource_app"
USER_ID = "student_user"

# --- Session and Runner Setup ---

def get_runner():
    """Create or retrieve the ADK runner from session state."""
    if "runner" not in st.session_state:
        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        
        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
            artifact_service=artifact_service
        )
        st.session_state.runner = runner
        st.session_state.session_service = session_service
    
    return st.session_state.runner


async def get_or_create_session():
    """Create a new ADK session or retrieve existing one (async)."""
    # Ensure runner (and thus session_service) exists first
    get_runner()
    
    session_service = st.session_state.session_service
    
    if "session_id" not in st.session_state:
        # create_session is async in current ADK
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID
        )
        st.session_state.session_id = session.id
    
    return st.session_state.session_id


def call_agent(prompt: str) -> str:
    """Send a message to the agent and get the response (synchronous wrapper)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(_call_agent_async(prompt))
    finally:
        loop.close()


async def _call_agent_async(prompt: str, max_retries: int = 3) -> str:
    """Async implementation of the agent call with retry logic.
    
    Handles 503 errors (high demand) by retrying with exponential backoff.
    
    Args:
        prompt: The user's question
        max_retries: Maximum number of attempts (default 3)
        
    Returns:
        The agent's response, or a graceful error message
    """
    import time
    
    runner = get_runner()
    session_id = await get_or_create_session()
    
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )
    
    for attempt in range(max_retries):
        try:
            response_text = ""
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=message
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_text += part.text
            
            if response_text:
                return response_text
                
        except Exception as e:
            error_str = str(e)
            
            # Check if this is a temporary overload error
            is_overloaded = any(
                keyword in error_str 
                for keyword in ["503", "UNAVAILABLE", "high demand", "overloaded"]
            )
            
            if is_overloaded and attempt < max_retries - 1:
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2 ** (attempt + 1)
                await asyncio.sleep(wait_time)
                continue
            elif is_overloaded:
                # We've exhausted all retries
                return "The service is temporarily busy. Please try again in a few minutes."
            else:
                # Different type of error - don't retry, let it surface
                raise
    
    return "I couldn't process that request."

# --- Streamlit UI ---

st.title("🏛️ Campus Resource Assistant")

st.markdown("""
Ask me about campus resources like the library, tutoring center, 
advising office, or financial aid. I can help you find hours, 
locations, and contact information.
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize response cache
if "response.cache" not in st.session_state:
    st.session_state.response_cache = {}

# Welcome message on first load
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("""
        👋 Hello! I'm your Campus Resource Assistant.
        
        I can help you find information about campus resources like:
        - 📚 **Library** - hours, location, services
        - ✏️ **Tutoring Center** - free academic support
        - 📋 **Academic Advising** - degree planning help
        - 💰 **Financial Aid** - grants, scholarships, FAFSA
        
        What would you like to know?
        """)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask about campus resources..."):
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response (check cache first)
    with st.chat_message("assistant"):
        # Normalize the prompt for cache lookup
        cache_key = prompt.lower().strip()
        
        if cache_key in st.session_state.response_cache:
            # Cache hit: serve instantly, no API call
            response = st.session_state.response_cache[cache_key]
            st.markdown(response)
            st.caption("⚡ Served from cache")
        else:
            # Cache miss: call the agent
            with st.spinner("Thinking..."):
                response = call_agent(prompt)
                st.markdown(response)
            
            # Store in cache for next time
            st.session_state.response_cache[cache_key] = response
    
    # Store assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar with information and controls
with st.sidebar:
    st.header("About")
    st.markdown(f"""
    This assistant helps you find information about campus resources.
    
    **Data source:** `{RESOURCE_FILE.name}`
    
    **Tip:** Try asking:
    - "Where is the library?"
    - "When is tutoring open?"
    - "What resources are available?"
    """)
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.session_state.response_cache = {}  # Clear cache too
        if "session_id" in st.session_state:
            del st.session_state.session_id
        st.rerun()