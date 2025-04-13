from fastapi import APIRouter, Form, Request, Depends, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timezone
from db.requests import *
from db.database import create_pool

from services.auth import AuthService

import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/request_authority")
async def submit_authority_request(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    details: str = Form(...),
    resume: UploadFile = File(...),
    auth_service: AuthService = Depends(AuthService),
    pool: aiomysql.Pool = Depends(create_pool)
):
    try:

        user_id = auth_service.is_authenticated(request)
        now = datetime.now(timezone.utc)
        
        recent = await most_recent_authority_rq(pool, user_id, title)
        
        if recent:
            last_timestamp = recent[0]
            if last_timestamp and last_timestamp.tzinfo is None:
                last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

            if last_timestamp and (now - last_timestamp).days < 30:
                return templates.TemplateResponse("authority.html", {
                    "request": request,
                    "error": "You’ve already submitted a request with this title in the last 30 days."
                })

        resume_data = await resume.read()
        await add_authority_rq(pool, user_id, title, category, details, resume_data)

        return templates.TemplateResponse("authority.html", {
            "request": request,
            "success": "Request submitted successfully and stored in the database!"
        })

    except Exception as e:
        return templates.TemplateResponse("authority.html", {
            "request": request,
            "error": f"An unknown error occurred. Contact admin: {e}"
        })

@router.get("/request_authority", response_class=HTMLResponse)
async def request_authority_form(request: Request):
    return templates.TemplateResponse("authority.html", {"request": request})
