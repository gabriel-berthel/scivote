from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from db.database import create_pool
from services.vector_search import VectorSearch
from db.requests import *
from services.utils import *
from cachetools import TTLCache
from models.search_request import SearchRequest
from datetime import datetime

router = APIRouter(prefix="/api")

SEARCH_CACHE = TTLCache(maxsize=500, ttl=60)
ARTICLE_CACHE = TTLCache(maxsize=1000, ttl=2592000)
SCORE_CACHE = TTLCache(maxsize=1000, ttl=60)
RATE_LIMIT_CACHE = TTLCache(maxsize=1000, ttl=60)
RATE_LIMIT = 10

@router.post("/search/")
async def search_documents(
    request: Request,
    search: SearchRequest, 
    vector_search_service: VectorSearch = Depends(VectorSearch), 
    pool = Depends(create_pool),
):
    user_ip = request.client.host
    
    # Rate limiting logic
    if user_ip in RATE_LIMIT_CACHE:
        if RATE_LIMIT_CACHE[user_ip] >= RATE_LIMIT:
            return JSONResponse(
                status_code=429, 
                content={"status": "error", "message": "Rate limit exceeded. Try again later."}
            )
        RATE_LIMIT_CACHE[user_ip] += 1
    else:
        RATE_LIMIT_CACHE[user_ip] = 1

    cache_key = f"{search.query}:{search.get_category_filter()}:{search.top_k}"
    cached_result = SEARCH_CACHE.get(cache_key)

    if cached_result:
        return JSONResponse(
            status_code=200,
            content={"status": "success", "results": cached_result}
        )
    
    top_k = search.top_k if search.top_k <= 100 else 100

    try:
        search_results = vector_search_service.search_documents(
            search.query, category_filter=search.get_category_filter(), max_results=top_k
        )
        
        results = []

        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for result in search_results:
                    if isinstance(result, dict) and 'id' in result:
                        arxiv_id = result['id']

                        article = ARTICLE_CACHE.get(arxiv_id)
                        if not article:
                            article = await fetch_article_by_id(arxiv_id, pool)
                            ARTICLE_CACHE[arxiv_id] = article

                        scores = SCORE_CACHE.get(arxiv_id)
                        if not scores:
                            scores = await fetch_aggregate_scores_by_id(arxiv_id, pool)
                            SCORE_CACHE[arxiv_id] = scores
                        
                        if scores:
                            result_data = {
                                "title": article['title'],
                                "id": arxiv_id,
                                "abstract": article['abstract'],
                                "baseScore": result.get('score', 0),
                                "recency": timestamp_to_score(article['published']),
                                "authority": sigmoid(scores['authority_score']),
                                "truthworthiness": sigmoid(scores['truthworthiness_score']),
                                "sentiment": sigmoid(scores['sentiment_score']),
                                "conciseness": sigmoid(scores['conciseness_score']),
                                "readability": sigmoid(scores['readability_score']),
                                "transparency": sigmoid(scores['transparency_score'])
                            }
                            results.append(result_data)
                    else:
                        return JSONResponse(
                            status_code=400,
                            content={"status": "error", "detail": "Each search result must be a dictionary with 'id'."}
                        )

        SEARCH_CACHE[cache_key] = results
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "results": results}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )
