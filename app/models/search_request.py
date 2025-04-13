from pydantic import BaseModel, Field, field_validator
from typing import Optional
from services.utils import *
import re

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: Optional[int] = Field(default=5, le=100)

    @field_validator('category')
    def validate_category(cls, v):
        if v and v not in MAIN_CATEGORIES:
            raise ValueError(f"Invalid main category '{v}'. Must be one of: {', '.join(MAIN_CATEGORIES)}")
        return v
    
    @field_validator('query')
    def normalize_query(cls, v):
        v = v.strip()
        v = re.sub(r'\s+', ' ', v)
        return v.lower()

    def get_category_filter(self):
        if self.category:
            return f"{self.category}.*"
        return None