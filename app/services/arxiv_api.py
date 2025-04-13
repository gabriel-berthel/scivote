from fastapi import HTTPException
import arxiv
import re
from models.arxiv_document import ArxivDocument

class ArxivAPIService:
    def __init__(self):
        pass
    
    async def article_exists_on_arxiv(self, arxiv_id: str) -> bool:
        try:
            search = arxiv.Search(query=f"id:{arxiv_id}", max_results=1)
            results = list(search.results())
            return len(results) > 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error checking article on Arxiv: {str(e)}")

    def sanitize_arxiv_id(self, arxiv_id: str) -> str:
        arxiv_id = arxiv_id.strip().strip('"')
        arxiv_id = re.sub(r'^arxiv:\s*', '', arxiv_id, flags=re.IGNORECASE)
        arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
        return arxiv_id

    async def fetch_article_details(self, arxiv_id: str) -> ArxivDocument:
        try:
            search = arxiv.Search(query=f"id:{arxiv_id}", max_results=1)
            results = list(search.results())
            if results:
                return ArxivDocument.from_arxiv_id(arxiv_id)
            raise HTTPException(status_code=404, detail=f"Article with ID {arxiv_id} not found.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching article from Arxiv: {str(e)}")
    
    async def fetch_article_by_arxiv_id(self, arxiv_id: str) -> ArxivDocument:
        arxiv_id = self.sanitize_arxiv_id(arxiv_id)
        return await self.fetch_article_details(arxiv_id)
