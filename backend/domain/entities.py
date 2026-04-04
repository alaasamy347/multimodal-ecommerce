from pydantic import BaseModel
from typing import Optional, List

class Product(BaseModel):
    id: int
    name: str
    category: str
    subCategory: str
    image: str
    color: str
    has_3d_model: bool
    image_url: str
    model_url: Optional[str] = None
    glb_path: Optional[str] = None

class SearchResult(BaseModel):
    product: Product
    score: float

class MultimodalQuery(BaseModel):
    typed_query: Optional[str] = None
    voice_query: Optional[str] = None
    image_path: Optional[str] = None
    color_filter: Optional[str] = None
    top_k: int = 10

class SearchResponse(BaseModel):
    query: str
    interpreted_query: str
    typed_query: str
    voice_query: str
    voice_error: Optional[str]
    accurate_results: List[dict]
    related_results: List[dict]
    total_results: int
    color_filter: Optional[str]
    search_mode: str
    ai_summary: str
