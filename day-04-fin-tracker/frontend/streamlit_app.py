import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="💰 Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    .bot-message {
        background-color: #f0f8e8;
        border-left-color: #2ca02c;
    }
    .sidebar-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

def call_backend(user_input):
    """Call the FastAPI backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/chat", params={"user_input": user_input})
        if response.status_code == 200:
            return response.json()
        else:
            return {"bot": "Sorry, I'm having trouble connecting to the backend. Please make sure the server is running."}
    except requests.exceptions.ConnectionError:
        return {"bot": "❌ Cannot connect to backend. Please start the FastAPI server first:\n\n```bash\ncd backend\npython -m uvicorn app:app --reload\n```"}
    except Exception as e:
        return {"bot": f"Error: {str(e)}"}

# Initialize session state
if "messages" in st.session_state:
    messages = st.session_state.messages
else:
    messages = []
    st.session_state.messages = messages

if "backend_status" not in st.session_state:
    st.session_state.backend_status = "unknown"

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Quick Actions")
    
    # Backend status check
    if st.button("🔄 Check Backend Status"):
        try:
            response = requests.get(f"{BACKEND_URL}/chat", params={"user_input": "hello"})
            if response.status_code == 200:
                st.session_state.backend_status = "connected"
                st.success("✅ Backend Connected")
            else:
                st.session_state.backend_status = "error"
                st.error("❌ Backend Error")
        except:
            st.session_state.backend_status = "disconnected"
            st.error("❌ Backend Disconnected")
    
    # Quick action buttons
    quick_actions = [
        ("🚀 Start Data Gathering", "start data gathering"),
        ("📊 Check Status", "get data status"),
        ("💵 Add Income", "I want to add income"),
        ("💸 Add Expense", "I want to add an expense"),
        ("🏦 Add Loan Payment", "I want to add a loan payment"),
        ("📈 Get Summary", "get expense summary"),
        ("❓ Help", "help"),
    ]
    
    st.markdown("#### 🎛️ Quick Commands")
    for action_name, action_command in quick_actions:
        if st.button(action_name, key=f"quick_{action_command}"):
            # Add to chat
            messages.append({"role": "user", "content": action_command})
            response = call_backend(action_command)
            messages.append({"role": "bot", "content": response["bot"]})
            st.session_state.messages = messages
            st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Information panel
    st.markdown("### 📚 How to Use")
    st.markdown("""
    <div class="sidebar-info">
    <strong>💬 Chat Commands:</strong>
    <ul>
        <li>"start data gathering" - Begin tracking</li>
        <li>"I earn $5000 monthly" - Add income</li>
        <li>"I spend $1200 on rent" - Add expense</li>
        <li>"I pay $300 car loan" - Add loan</li>
        <li>"get expense summary" - View summary</li>
    </ul>
    
    <strong>📊 Categories:</strong>
    <ul>
        <li>🏠 Housing</li>
        <li>🍔 Food</li>
        <li>🚗 Transportation</li>
        <li>🏥 Healthcare</li>
        <li>🎬 Entertainment</li>
        <li>⚡ Utilities</li>
        <li>💳 Debt</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# Main chat interface
st.markdown('<h1 class="main-header">💰 Personal Finance Tracker</h1>', unsafe_allow_html=True)

# Chat container
chat_container = st.container()

with chat_container:
    # Display welcome message if no chat history
    if not messages:
        st.markdown("""
        <div class="chat-message bot-message">
            <strong>🤖 Finance Bot:</strong><br>
            Welcome to your Personal Finance Tracker! 🎉<br><br>
            
            I can help you:
            <ul>
                <li>📊 Track your income and expenses</li>
                <li>🏦 Record loan payments</li>
                <li>📈 Generate financial summaries</li>
                <li>💡 Provide general budgeting tips</li>
            </ul>
            
            <strong>🚀 Get started by saying "start data gathering" or click the quick action buttons in the sidebar!</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Format bot response with proper line breaks and styling
            bot_content = message["content"].replace("\n", "<br>")
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Finance Bot:</strong><br>
                {bot_content}
            </div>
            """, unsafe_allow_html=True)

# Chat input
st.markdown("---")
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input(
        "💬 Type your message:", 
        placeholder="e.g., 'I earn $5000 monthly' or 'start data gathering'",
        key="chat_input"
    )

with col2:
    send_button = st.button("🚀 Send", type="primary")

# Handle message sending
if send_button and user_input:
    # Add user message
    messages.append({"role": "user", "content": user_input})
    
    # Get bot response
    with st.spinner("🤔 Thinking..."):
        response = call_backend(user_input)
    
    # Add bot response
    messages.append({"role": "bot", "content": response["bot"]})
    
    # Update session state
    st.session_state.messages = messages
    
    # Rerun to show new messages
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    💰 Personal Finance Tracker powered by Parlant AI | 
    🔒 Your data is private and secure | 
    📝 For tracking only, not financial advice
</div>
""", unsafe_allow_html=True)

# Auto-scroll to bottom (JavaScript)
st.markdown("""
<script>
var element = document.getElementById("main");
element.scrollTop = element.scrollHeight;
</script>
""", unsafe_allow_html=True)
