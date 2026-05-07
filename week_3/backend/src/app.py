from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Helper Backend")

# Allow cross-origin for development. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: Optional[str] = ""
    pdf_text: Optional[str] = ""
    filename: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    message: str
    details: Optional[dict] = None


@app.get("/chat")
async def chat_get(request: Request):
    """Health / info endpoint for the chat route."""
    return JSONResponse({"status": "ok", "route": "/chat", "method": "POST"})


@app.post("/chat", response_model=ChatResponse)
async def chat_post(payload: ChatRequest):
    """
    Receive a JSON payload from the frontend containing:
      - message: user prompt
      - pdf_text: extracted text from uploaded PDF
      - filename: optional filename

    For now this endpoint performs basic validation and echoes back a summary.
    Later it will call the skill-gap logic / LLM pipelines.
    """
    try:
        logger.info("Received chat payload: filename=%s, message_len=%d, pdf_len=%d",
                    payload.filename,
                    len(payload.message or ""),
                    len(payload.pdf_text or ""))

        # Deterministic placeholder logic: compute simple statistics
        char_count = len((payload.message or "")) + len((payload.pdf_text or ""))
        word_count = len(((payload.pdf_text or "") + " " + (payload.message or "")).split())

        details = {
            "filename": payload.filename,
            "char_count": char_count,
            "word_count": word_count,
        }

        return ChatResponse(status="ok", message="Payload received", details=details)

    except Exception as e:
        logger.exception("Error processing chat payload")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
