import aiomysql
from models.arxiv_document import ArxivDocument
from datetime import datetime, timedelta

async def article_exists(pool, arxiv_id: str):
    query = "SELECT * FROM arxiv_articles WHERE id = %s"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (arxiv_id,))
            db_data = await cursor.fetchone()
            return db_data is not None

async def insert_article(pool, document: ArxivDocument, pdf_url: str, arxiv_url: str):
    insert_query = """
        INSERT INTO arxiv_articles (id, title, abstract, authors, categories, published, pdf_url, arxiv_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Acquire a connection from the pool
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(insert_query, 
                                 (document.arxiv_id, 
                                  document.title, 
                                  document.abstract, 
                                  ", ".join(document.authors),
                                  ", ".join(document.categories) if document.categories else "",
                                  document.published, 
                                  pdf_url, 
                                  arxiv_url))

async def fetch_aggregate_scores_by_id(arxiv_id: str, pool):
    query = """
    SELECT
        a.article_id,
        a.authority_score, 
        a.truthworthiness_score, a.sentiment_score, a.conciseness_score,
        a.readability_score, a.transparency_score
    FROM article_score_aggregates a
    WHERE a.article_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (arxiv_id,))
            return await cursor.fetchone()

async def fetch_article_by_id(arxiv_id: str, pool):
    query = """
    SELECT
        a.id AS article_id, a.title, a.abstract, a.published, a.authors, a.categories,
        0 AS authority_score, 
        0 AS truthworthiness_score, 0 AS sentiment_score, 0 AS conciseness_score,
        0 AS readability_score, 0 AS transparency_score
    FROM arxiv_articles a
    WHERE a.id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, (arxiv_id,))
            return await cursor.fetchone()

async def has_voted_recently(pool, user_id: int, article_id: str):
    
    last_vote = await has_voted(pool, user_id, article_id)

    if last_vote:
        time_difference = datetime.now() - last_vote
        
        return time_difference < timedelta(days=30)

    return False

async def has_voted(pool, user_id: int, article_id: str):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("""
                    SELECT created_at 
                    FROM article_votes 
                    WHERE user_id = %s AND article_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (user_id, article_id))
                
                result = await cur.fetchone()

                if result:
                    return result[0]
                
            except Exception as e:
                print(f"Error checking vote: {e}")
                return False
                    
    return False

async def get_user_multiplier(pool, user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("""
                    SELECT score_multiplier 
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
                result = await cur.fetchone()
                print(result)
                return result[0]
            
            except Exception as e:
                return 0.1


async def get_existing_vote(pool, user_id: int, arxiv_id: str):
    select_query = """
    SELECT  authority_score, truthworthiness_score,
           sentiment_score, conciseness_score, readability_score, transparency_score
    FROM article_votes
    WHERE user_id = %s AND article_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(select_query, (user_id, arxiv_id))
            return await cursor.fetchone()


async def subtract_old_scores_from_aggregate(pool, arxiv_id: str, old_scores: tuple):
    update_query_subtract = """
    UPDATE article_score_aggregates
    SET
        authority_score = authority_score - %s,
        truthworthiness_score = truthworthiness_score - %s,
        sentiment_score = sentiment_score - %s,
        conciseness_score = conciseness_score - %s,
        readability_score = readability_score - %s,
        transparency_score = transparency_score - %s
    WHERE article_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(update_query_subtract, (
                old_scores[0], old_scores[1], old_scores[2], old_scores[3],
                old_scores[4], old_scores[5], arxiv_id
            ))
            await conn.commit()


async def add_new_scores_to_aggregate(pool, arxiv_id: str, new_scores: tuple):
    update_query_add = """
    UPDATE article_score_aggregates
    SET
        authority_score = ROUND(authority_score + %s, 3),
        truthworthiness_score = ROUND(truthworthiness_score + %s, 3),
        sentiment_score = ROUND(sentiment_score + %s, 3),
        conciseness_score = ROUND(conciseness_score + %s, 3),
        readability_score = ROUND(readability_score + %s, 3),
        transparency_score = ROUND(transparency_score + %s, 3)
    WHERE article_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(update_query_add, (
                new_scores[0], new_scores[1], new_scores[2], new_scores[3],
                new_scores[4], new_scores[5], arxiv_id
            ))
            await conn.commit()

async def insert_article_vote(pool, user_id: int, arxiv_id: str, new_scores: tuple):
    insert_query = """
    INSERT INTO article_votes (
        user_id, article_id,
        authority_score, truthworthiness_score,
        sentiment_score, conciseness_score, readability_score,
        transparency_score, weight_multiplier
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(insert_query, (
                user_id, arxiv_id,
                new_scores[0], new_scores[1], new_scores[2],
                new_scores[3], new_scores[4], new_scores[5], 
                await get_user_multiplier(pool, user_id)
            ))
            await conn.commit()

async def update_article_vote(pool, user_id: int, arxiv_id: str, new_scores: tuple):
    update_query = """
    UPDATE article_votes
    SET
        authority_score = %s,
        truthworthiness_score = %s,
        sentiment_score = %s,
        conciseness_score = %s,
        readability_score = %s,
        transparency_score = %s,
        weight_multiplier = %s
    WHERE user_id = %s AND article_id = %s;
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(update_query, (
                new_scores[0], new_scores[1], new_scores[2],
                new_scores[3], new_scores[4], new_scores[5], await get_user_multiplier(pool, user_id), user_id, arxiv_id
            ))
            await conn.commit()
            
async def insert_article_score_aggregate(pool,  id: int):
    query = """
    INSERT INTO article_score_aggregates (
        article_id,
        authority_score, truthworthiness_score,
        sentiment_score, conciseness_score, readability_score,
        transparency_score
    )
    VALUES (%s, 0, 0, 0, 0, 0, 0);
    """
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (
                id
            ))
            await conn.commit()

async def add_authority_rq(pool, user_id, title, category, details, resume):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            query = """
            INSERT INTO authority_requests (user_id, title, category, details, resume)
            VALUES (%s, %s, %s, %s, %s)
            """
            await cur.execute(query, (user_id, title, category, details, resume))
            await conn.commit()
            
async def most_recent_authority_rq(pool, user_id, title):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT timestamp FROM authority_requests
                WHERE user_id = %s
                ORDER BY timestamp DESC LIMIT 1
            """, (user_id,))
            return await cur.fetchone()