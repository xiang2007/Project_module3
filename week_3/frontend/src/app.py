import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv


app = FastAPI()

load_dotenv()
backend_url = os.getenv("BACKEND_URL", "")

current_file_dir = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(current_file_dir, "templates")
templates = Jinja2Templates(directory=template_path)

@app.get("/", response_class=HTMLResponse)
async def read_items(request: Request):
    return templates.TemplateResponse(
        request,
        "chat_page.html",
        {"backend_url": backend_url},
    )