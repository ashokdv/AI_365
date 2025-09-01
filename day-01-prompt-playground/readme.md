# Day 1 — Prompt Playground App 🤖

A complete AI chatbot application with FastAPI backend and Streamlit frontend, powered by local Ollama models.

## 📋 Project Overview

- **Summary:** Web UI that sends prompts to a text-generation model and shows responses
- **Contract:** input = prompt text; output = model completion
- **Stack:** FastAPI + Streamlit + Ollama (local LLM)
- **Time:** 1-2 hours setup + development
- **Deliverable:** Full-stack chatbot with conversation history

## 🏗️ Architecture

```
┌─────────────────┐    HTTP POST     ┌─────────────────┐    HTTP POST    ┌─────────────────┐
│   Streamlit     │ ───────────────► │   FastAPI       │ ──────────────► │   Ollama        │
│   Frontend      │                  │   Backend       │                 │   (Local LLM)   │
│   Port: 8501    │ ◄─────────────── │   Port: 8000    │ ◄────────────── │   Port: 11434   │
└─────────────────┘    JSON Response └─────────────────┘   Chat Response └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ installed
- WSL2 (for Ollama on Windows) or Linux/macOS
- At least 8GB RAM (16GB+ recommended)

### 1. Install Ollama

#### On Windows (WSL2 - Recommended)
```bash
# In WSL terminal
curl -fsSL https://ollama.com/install.sh | sh

# Download a model (this will also start the server)
ollama run mistral
```

#### On Linux/macOS
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download and run a model
ollama run mistral
```

#### Verify Ollama Installation
```bash
# Check if Ollama is running
ollama list

# Test the API
curl http://localhost:11434/api/chat -d '{
  "model": "mistral",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": false
}'
```

### 2. Setup Python Environment

```bash
# Navigate to project directory
cd day-01-prompt-playground

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install fastapi uvicorn httpx python-dotenv

# Install frontend dependencies
pip install streamlit requests python-dotenv
```

### 3. Configure Environment Variables

Copy and customize the environment file:
```bash
cp .env.example .env
```

Edit `.env` file:
```properties
# API Configuration
API_BASE_URL=http://localhost:8000

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Frontend Configuration
STREAMLIT_PORT=8501
```

### 4. Run the Application

#### Terminal 1: Start Ollama (if not already running)
```bash
# Make sure Ollama server is running and listening on all interfaces
OLLAMA_HOST=0.0.0.0 ollama serve
```

#### Terminal 2: Start FastAPI Backend
```bash
# Navigate to project root
cd day-01-prompt-playground

# Start the API server
python -m uvicorn backend.api:app --reload --port 8000
```

#### Terminal 3: Start Streamlit Frontend
```bash
# Navigate to project root
cd day-01-prompt-playground

# Start the frontend
streamlit run frontend/app.py --server.port 8501
```

### 5. Access the Application

- **Streamlit Frontend:** http://localhost:8501
- **FastAPI Backend:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Ollama API:** http://localhost:11434

## 📁 Project Structure

```
day-01-prompt-playground/
├── backend/
│   └── api.py                 # FastAPI server with Ollama integration
├── frontend/
│   ├── app.py                 # Streamlit chatbot interface
│   ├── requirements.txt       # Frontend dependencies
│   └── README.md             # Frontend-specific docs
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Environment variables template
└── README.md               # This file
```

## 🔧 API Endpoints

### FastAPI Backend

- **POST `/generate`**
  ```json
  {
    "text": "Your prompt here",
    "model": "mistral"
  }
  ```
  
  Response:
  ```json
  {
    "response": "AI generated response"
  }
  ```

### Ollama API

- **POST `/api/chat`** - Chat completions
- **GET `/api/tags`** - List available models
- **POST `/api/pull`** - Download new models

## 🛠️ Available Models

Common Ollama models you can use:
- `mistral` - 7B parameters, good balance of speed/quality
- `llama2` - Meta's LLaMA 2 model
- `codellama` - Specialized for code generation
- `tinyllama` - Very fast, smaller model

To download a new model:
```bash
ollama pull <model-name>
```

## 🐛 Troubleshooting

### Ollama Issues

**"Connection refused" or "API Offline":**
```bash
# Check if Ollama is running
ollama list

# Restart Ollama server with network access
OLLAMA_HOST=0.0.0.0 ollama serve

# Verify the API responds
curl http://localhost:11434/api/tags
```

**Model not found:**
```bash
# Download the model
ollama pull mistral

# List available models
ollama list
```

### Performance Issues

**Slow responses:**
- Models run on CPU by default (slow)
- For GPU acceleration, ensure NVIDIA drivers are installed in WSL
- Try smaller models like `tinyllama` for faster responses
- Consider using cloud APIs for production use

### API Connection Issues

**Frontend can't connect to backend:**
- Verify FastAPI is running on port 8000
- Check `.env` file has correct `API_BASE_URL`
- Ensure no firewall blocking localhost connections

**Backend can't connect to Ollama:**
- Ensure Ollama is running: `ollama list`
- Try `OLLAMA_HOST=0.0.0.0 ollama serve`
- Check WSL2 networking if on Windows

## 🚀 Development

### Adding New Features

1. **New API endpoints:** Add to `backend/api.py`
2. **Frontend improvements:** Modify `frontend/app.py`
3. **Model configurations:** Update `.env` file

### Testing

```bash
# Test the API directly
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "model": "mistral"}'

# Test Ollama directly
curl http://localhost:11434/api/chat -d '{
  "model": "mistral",
  "messages": [{"role": "user", "content": "Test message"}],
  "stream": false
}'
```

## 📚 Next Projects

Day 2 — Tiny image captioner  
- Summary: upload image → get a caption from a vision+LLM model.  
- Contract: input = image; output = 1–2 captions; success = appropriate caption.  
- Stack: Python/Flask, Hugging Face Vision+Text or OpenAI Images+Vision.  
- Time: 2–3 hours.  
- Deliverable: upload UI + caption. Stretch: multilingual captions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the 30 Days of AI Apps series.


