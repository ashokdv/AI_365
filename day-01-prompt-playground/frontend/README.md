# Streamlit Frontend - Day 1 Prompt Playground

This is the Streamlit frontend for the Day 1 Prompt Playground application.

## Features

- 🤖 Clean chatbot interface
- 💬 Persistent chat history during session
- ⚙️ Model selection (mistral, llama2, codellama, tinyllama)
- 🔌 API connection status indicator
- 🗑️ Clear chat functionality
- 📱 Responsive design

## How to Run

1. **Install dependencies:**
   ```powershell
   pip install streamlit requests
   ```

2. **Make sure your FastAPI backend is running:**
   ```powershell
   python -m uvicorn backend.api:app --reload --port 8000
   ```

3. **Run the Streamlit app:**
   ```powershell
   streamlit run frontend/app.py
   ```

4. **Open your browser to:**
   - Streamlit app: http://localhost:8501
   - FastAPI docs: http://localhost:8000/docs

## Usage

1. Select your preferred model from the sidebar
2. Type your message in the chat input at the bottom
3. Press Enter or click Send
4. View the AI response in the chat
5. Use "Clear Chat" to start fresh

## Troubleshooting

- If you see "API Offline", make sure your FastAPI server is running on port 8000
- If responses are slow, it's likely due to CPU-only inference (see main README for GPU setup)
- Check that Ollama is running with the selected model available
