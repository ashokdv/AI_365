from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, AsyncGenerator
from PIL import Image
import io
import httpx
import base64
import json
import asyncio

LLM_URL = "http://localhost:11434/api/generate"

app = FastAPI(title="Tiny Image Upload API")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Max upload size to protect the server (10 MB)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
# allowed mime types and PIL formats
ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/jpg", "image/png")
ALLOWED_FORMATS = ("JPEG", "PNG")


@app.get("/")
async def root() -> Dict[str, str]:
    return {"status": "ok", "message": "POST /upload with form field 'file' (image)"}



@app.post("/upload_stream")
async def upload_image_stream(file: UploadFile = File(...)):
    """Upload an image and stream the caption from the LLM.
    
    Request: form field named 'file' containing the image.
    Response: Streaming response with text/event-stream media type.
    """
    # basic content-type check (restrict to jpeg/jpg/png)
    if not file.content_type or file.content_type.lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Uploaded file must be jpeg/jpg/png")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        img = Image.open(io.BytesIO(data))
        width, height = img.size
        fmt = img.format
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot process image: {e}")

    # enforce allowed image formats (Pillow format names)
    if not fmt or fmt.upper() not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Only JPEG/JPG and PNG images are allowed")

    async def stream_response():
        try:
            b64 = base64.b64encode(data).decode("utf-8")
            payload = {
                "model": "llava",
                "prompt": "Describe the image followed by Captionize the picture in few words, give atleast two captions for the picture",
                "images": [b64],
                "stream": True  # Ensure we get a streaming response
            }
            
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", LLM_URL, json=payload) as response:
                    if response.status_code >= 400:
                        error_text = await response.aread()
                        yield f"data: {{\"error\": \"{error_text}\" }}\n\n"
                        return
                        
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            # Each chunk is a JSON object with text token
                            yield f"data: {chunk.decode('utf-8')}\n\n"
        
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\" }}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )