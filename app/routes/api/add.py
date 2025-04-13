from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from services.arxiv_api import ArxivAPIService
from services.vector_search import VectorSearch
from db.database import create_pool
from db.requests import article_exists, insert_article, insert_article_score_aggregate
from cachetools import TTLCache
import asyncio

router = APIRouter(prefix="/api")
RATE_LIMIT = 5
RATE_LIMIT_CACHE = TTLCache(maxsize=1000, ttl=60)
ANSWER_CACHE = TTLCache(maxsize=500, ttl=86400)

@router.get("/add/{arxiv_id:path}")
async def add_arxiv_document(
    request: Request,
    arxiv_id: str, 
    pool = Depends(create_pool), 
    arxiv_service = Depends(ArxivAPIService),
    vector_search_service = Depends(VectorSearch)
):
    ip = request.client.host
    
    if ip in RATE_LIMIT_CACHE:
        if RATE_LIMIT_CACHE[ip] >= RATE_LIMIT:
            return JSONResponse(content={"status": "error", "message": "Rate limit exceeded"})
        RATE_LIMIT_CACHE[ip] += 1
    else:
        RATE_LIMIT_CACHE[ip] = 1
        
    await asyncio.sleep(1.5)

    if arxiv_id in ANSWER_CACHE:
        return JSONResponse(content=ANSWER_CACHE[arxiv_id])

    try:
        arxiv_id = arxiv_service.sanitize_arxiv_id(arxiv_id)

        if await article_exists(pool, arxiv_id):
            return JSONResponse(content={"status": "error", "message": "Article already exists in the database", "id": arxiv_id})
        
        if not await arxiv_service.article_exists_on_arxiv(arxiv_id):
            return JSONResponse(content={"status": "error", "message": "Article does not exist on Arxiv", "id": arxiv_id})
        
        document = await arxiv_service.fetch_article_by_arxiv_id(arxiv_id)

        vector_search_service.insert_document(document)

        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

        await insert_article(pool, document, pdf_url, arxiv_url)
        await insert_article_score_aggregate(pool, arxiv_id)
        
        response = {
            "status": "success",
            "message": f"Article added successfully. It can take several minutes for the addition to be reflected in the search!",
            "id": document.arxiv_id,
            "title": document.title
        }

        ANSWER_CACHE[arxiv_id] = response

        return JSONResponse(content=response)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
