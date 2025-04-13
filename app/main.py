from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from routes import auth, authority, view, grade
from routes.api import add, search
import os

app = FastAPI()

origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(authority.router)
app.include_router(view.router)
app.include_router(grade.router)
app.include_router(add.router)
app.include_router(search.router)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Exception Handler -> Redirects to error pages.
@app.exception_handler(HTTPException)
async def custom_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return templates.TemplateResponse("auth_fail.html", {"request": request})
    
    elif exc.status_code == 404:
        return templates.TemplateResponse(
            "defaut_error.html",
            {"request": request, "detail": exc.detail}
        )
    
    return HTMLResponse(status_code=exc.status_code, content=f"Error: {exc.detail}")

# Fallback route if nothing else works.
@app.get("/{path_name:path}")
async def fallback(request: Request, path_name: str):
    return templates.TemplateResponse("not_found.html", {"request": request})