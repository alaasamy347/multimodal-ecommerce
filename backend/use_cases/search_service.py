from typing import Optional, List
from domain.entities import MultimodalQuery, SearchResponse

class SearchService:
    def __init__(self, transcription_service, model_framework, database_framework, ollama_framework):
        self.transcriber = transcription_service
        self.model = model_framework
        self.db = database_framework
        self.ollama = ollama_framework
        
    async def process_multimodal_query(self, query: MultimodalQuery) -> SearchResponse:
        # 1. Transcribe voice if present
        voice_text = ""
        voice_error = None
        if query.voice_query:
            voice_text, voice_error = await self.transcriber.transcribe(query.voice_query)
            
        # 2. Extract intents/refine query using local LLM (Unified Understanding Engine)
        raw_query = f"{voice_text} {query.typed_query or ''}".strip()
        interpreted_query = raw_query
        ai_summary = ""
        
        if raw_query:
            prompt = f"Extract furniture search keywords from this user query: '{raw_query}'. Return only the keywords."
            interpreted_query = await self.ollama.generate(prompt)
            
        # 3. Visual Reasoning (if image and question)
        if query.image_path and raw_query:
            vision_prompt = f"Analyze this image and answer: {raw_query}"
            ai_summary = await self.ollama.vision_reasoning(vision_prompt, query.image_path)
        
        # 4. Get Embeddings (SigLIP via framework)
        vectors = await self.model.get_embeddings(interpreted_query, query.image_path)
        
        # 5. Search Vector DB
        results = await self.db.search_vectors(vectors, top_k=query.top_k, color=query.color_filter)
        
        if not ai_summary:
            ai_summary = f"Found {len(results)} items matching your requirement."

        return SearchResponse(
            query=raw_query,
            interpreted_query=interpreted_query or raw_query,
            typed_query=query.typed_query or "",
            voice_query=voice_text,
            voice_error=voice_error,
            accurate_results=[r["product"] for r in results],
            related_results=[],
            total_results=len(results),
            color_filter=query.color_filter,
            search_mode="multimodal",
            ai_summary=ai_summary
        )
