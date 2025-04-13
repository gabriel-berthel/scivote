from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from db.database import create_pool
from db.requests import *
from services.auth import AuthService

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/view/{arxiv_id:path}", response_class=HTMLResponse)
async def view_article(
    request: Request,
    arxiv_id: str,
    pool: any = Depends(create_pool),
    auth_service: AuthService = Depends(AuthService)
):
    
    if not await article_exists(pool, arxiv_id):
        raise HTTPException(
            status_code=404,
            detail=f"Article with ID {arxiv_id} does not exist in the database. Please add it on the proper page."
        )

    article_scores = await fetch_aggregate_scores_by_id(arxiv_id, pool)
    article = await fetch_article_by_id(arxiv_id, pool)

    try:
        user_id = auth_service.is_authenticated(request)
        return templates.TemplateResponse("arxiv-article.html", {
            "request": request,
            "article": article,
            "scores": article_scores,
            "user_logged_in": True,
            "user_has_graded": await has_voted(pool, user_id, arxiv_id),
            "user_has_graded_recently": await has_voted_recently(pool, user_id, arxiv_id),
        })
    except Exception as e:
        return templates.TemplateResponse("arxiv-article.html", {
            "request": request,
            "article": article,
            "scores": article_scores,
            "user_logged_in": False,
            "user_has_graded": False,
        })
