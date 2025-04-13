from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.auth import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def get_register_form(request: Request, auth_service: AuthService = Depends(AuthService)):
    try:
        auth_service.is_authenticated(request)
        return RedirectResponse(url="/", status_code=303)
    except HTTPException:
        return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def post_register_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    auth_service: AuthService = Depends()
):
    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Password must be at least 6 characters long."
        })
    
    if password != password_confirm:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match."
        })
    
    try:
        await auth_service.register_user(email, password)
        return RedirectResponse(url="/login", status_code=302)
    
    except HTTPException as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Failed to register: " + str(e.detail)
        })
    
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "An unexpected error occurred: " + str(e)
        })

@router.get("/login", response_class=HTMLResponse)
async def get_login_form(request: Request, auth_service: AuthService = Depends(AuthService)):
    try:
        auth_service.is_authenticated(request)
        return RedirectResponse(url="/", status_code=303)
    except HTTPException:
        return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def post_login_form(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends()
):
    try:
        user_id = await auth_service.authenticate_user(email, password)
        signed_user_id = auth_service.serializer.dumps(user_id)
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="user_id", 
            value=signed_user_id, 
            expires=3600, 
            httponly=True, 
            secure=False, 
            path="/",
            samesite="Lax"
        )
        return response
    except HTTPException:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })

@router.get("/logout")
async def logout(request: Request, response: RedirectResponse):
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(key="user_id")
    return response
