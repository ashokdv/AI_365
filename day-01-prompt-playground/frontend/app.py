import streamlit as st
import requests
import json
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="Prompt Playground",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration from environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def call_api(text: str, model: str = "mistral") -> Optional[str]:
    """Call the FastAPI backend to generate a response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/generate",
            json={"text": text, "model": model},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response")
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model selection
    selected_model = st.selectbox(
        "Choose Model",
        ["mistral", "llama2", "codellama", "tinyllama"],
        index=0 if DEFAULT_MODEL == "mistral" else 0,
        help="Select the Ollama model to use"
    )
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # API status check
    st.subheader("🔌 API Status")
    st.caption(f"Connecting to: {API_BASE_URL}")
    try:
        health_response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline")
    
    st.markdown("---")
    st.markdown("""
    ### 📖 How to use:
    1. Make sure your FastAPI server is running on port 8000
    2. Ensure Ollama is running with the selected model
    3. Type your message and press Enter or click Send
    4. Chat history is maintained during the session
    """)

# Main chat interface
st.title("🤖 Prompt Playground")
st.markdown("Chat with your local AI models via Ollama!")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = call_api(prompt, selected_model)
            
        if response:
            st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            error_msg = "Sorry, I couldn't generate a response. Please check if the API and Ollama are running."
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        💡 Powered by FastAPI, Streamlit, and Ollama | 
        <a href='http://localhost:8000/docs' target='_blank'>API Docs</a>
    </div>
    """, 
    unsafe_allow_html=True
)
