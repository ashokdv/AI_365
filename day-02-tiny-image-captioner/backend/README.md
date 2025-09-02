Tiny Image Upload API

This folder contains a minimal FastAPI app that accepts an image upload and returns basic metadata.

How to run (Windows PowerShell):

1. Create & activate a virtual environment

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

3. Start the server

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

Try it: POST an image to http://127.0.0.1:8000/upload using curl or a client like Postman.
