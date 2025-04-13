from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db.database import create_pool
from services.auth import AuthService
from db.requests import *

router = APIRouter()
templates = Jinja2Templates(directory="templates")

async def check_article_and_vote_status(request: Request, arxiv_id: str, pool: any = Depends(create_pool), auth_service: AuthService = Depends(AuthService)):
    user_id = auth_service.is_authenticated(request)

    if not await article_exists(pool, arxiv_id):
        raise HTTPException(status_code=404, detail=f"Article with ID {arxiv_id} does not exist in the database. Please add it on the proper page.")
    
    if await has_voted_recently(pool, user_id, arxiv_id):
        raise HTTPException(status_code=404, detail=f"You already voted for {arxiv_id}. You can only vote once every 30 days.")
    
    return user_id

@router.get("/grade/{arxiv_id:path}", response_class=HTMLResponse)
async def show_grade_form(request: Request, arxiv_id: str, user_id: str = Depends(check_article_and_vote_status)):
    article = {"id": arxiv_id}
    return templates.TemplateResponse("grade-article.html", {"request": request, "article": article})

@router.post("/grade/{arxiv_id:path}")
async def submit_grade(
    request: Request,
    arxiv_id: str,
    authority_score: float = Form(...),
    truthworthiness_score: float = Form(...),
    sentiment_score: float = Form(...),
    conciseness_score: float = Form(...),
    readability_score: float = Form(...),
    transparency_score: float = Form(...),
    user_id: str = Depends(check_article_and_vote_status),
    pool: any = Depends(create_pool)
):
    try:
        existing_vote = await get_existing_vote(pool, user_id, arxiv_id)
        new_scores = (authority_score, truthworthiness_score, sentiment_score, conciseness_score, readability_score, transparency_score)

        if existing_vote:
            await update_article_vote(pool, user_id, arxiv_id, new_scores)
            await subtract_old_scores_from_aggregate(pool, arxiv_id, existing_vote)
            await add_new_scores_to_aggregate(pool, arxiv_id, new_scores)
        else:
            await insert_article_vote(pool, user_id, arxiv_id, new_scores)
            await add_new_scores_to_aggregate(pool, arxiv_id, new_scores)

        return RedirectResponse(
            url=f"/view/{arxiv_id}",
            status_code=303
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "grade-article.html",
            {"request": request, "error": f"An unknown error occurred {e}. Please try again later.", "article": {"id": arxiv_id}}
        )
