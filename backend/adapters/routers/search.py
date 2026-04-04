from fastapi import APIRouter, File, Form, UploadFile, Depends
from typing import Optional
import tempfile
import os

from domain.entities import MultimodalQuery, SearchResponse
from use_cases.search_service import SearchService

router = APIRouter()

# Dependency override for search service (this will be injected in main.py)
def get_search_service() -> SearchService:
    raise NotImplementedError

@router.post("/search/intelligent", response_model=SearchResponse)
async def intelligent_search(
    query: Optional[str] = Form(""),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    top_k: int = Form(10),
    search_service: SearchService = Depends(get_search_service)
):
    tmp_audio = None
    tmp_img = None
    
    # Save audio temporarily
    if audio:
        data = await audio.read()
        if len(data) > 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(data)
                tmp_audio = f.name
                
    # Save image temporarily
    if image:
        data = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(data)
            tmp_img = f.name
            
    # Execute use case
    multimodal_query = MultimodalQuery(
        typed_query=query,
        voice_query=tmp_audio,
        image_path=tmp_img,
        top_k=top_k
    )
    
    result = await search_service.process_multimodal_query(multimodal_query)
    
    # Cleanup temp files
    for tmp in [tmp_audio, tmp_img]:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
            
    return result
