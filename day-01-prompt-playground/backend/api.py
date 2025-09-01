from fastapi import FastAPI
from pydantic import BaseModel
import os
import httpx
import json
from typing import Optional

app = FastAPI(title="Prompt Playground API")


class PromptIn(BaseModel):
	text: str
	model: str = "mistral"


class CompletionOut(BaseModel):
	response: Optional[str] = None


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


async def call_ollama_chat(prompt_text: str, model: str, timeout: Optional[float] = 300.0) -> Optional[str]:
	"""Call the Ollama local HTTP API /api/chat and return the generated text.

	Expects Ollama running locally (default http://localhost:11434).
	"""
	url = f"{OLLAMA_URL}/api/chat"
	payload = {
		"model": model,
		"messages": [
			{"role": "user", "content": prompt_text}
		],
		"stream": False
	}

	headers = {
        "Content-Type": "application/json",
    }

	try:
		async with httpx.AsyncClient(timeout=timeout) as client:
			response = await client.post(url, json=payload, headers=headers)
			response.raise_for_status()

			result = response.json()

			# Extract the assistant's message content
			if "message" in result and "content" in result["message"]:
				return result["message"]["content"]
			else:
				return None
                
	except Exception as e:
		print(f"Error calling Ollama API: {e}")
		return None



	
@app.post("/generate", response_model=CompletionOut)
async def generate(prompt: PromptIn):
	"""Accepts JSON {"text": "..."} and returns a generated completion from Ollama.

	Falls back to an echo response if Ollama is unreachable or the call fails.
	"""
	user_text = prompt.text or ""
	model = prompt.model or "mistral"
	generated = await call_ollama_chat(user_text, model)
	if not generated:
		generated = f"{user_text}"
	return CompletionOut(response=generated)


# To run locally for development:
# 1) pip install fastapi uvicorn httpx
# 2) Start Ollama locally and ensure the model is available (see https://ollama.com)
# 3) uvicorn backend.api:app --reload --port 8000
