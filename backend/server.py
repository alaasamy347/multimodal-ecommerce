print("DEBUG: server.py starting imports...")
from fastapi import FastAPI
print("DEBUG: FastAPI imported")
from fastapi.middleware.cors import CORSMiddleware
print("DEBUG: CORS imported")

# Adapters
from adapters.routers import search as search_router
print("DEBUG: Search router imported")
from adapters.routers import checkout as checkout_router
print("DEBUG: Checkout router imported")
from adapters.db.models import get_engine, init_db
print("DEBUG: Models imported")

# Use Cases
from use_cases.search_service import SearchService
print("DEBUG: Search Service imported")
from use_cases.transcription_service import TranscriptionService
print("DEBUG: Transcription Service imported")
from use_cases.checkout_service import CheckoutService
print("DEBUG: Checkout Service imported")

# Frameworks
from frameworks.interfaces import ModelFramework, WhisperFramework, DatabaseFramework, OllamaFramework
print("DEBUG: Interfaces imported")
from pathlib import Path
print("DEBUG: Path imported")

app = FastAPI(title="Multimodal E-Commerce API")

_base = Path(__file__).parent
DATA_DIR = _base / "data"
PRODUCTS_PATH = str(DATA_DIR / "clean_products.json")
CHROMA_PATH = str(DATA_DIR / "chroma_db")
ID_MAP_PATH = str(DATA_DIR / "id_map.npy")
INDEX_PATH = str(DATA_DIR / "image_index.faiss")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (Singletons with Lazy Init)
_services = {}

def get_services():
    if not _services:
        print("DEBUG: Lizily initializing services...")
        try:
            # Re-import everything inside to be extra safe
            from adapters.db.models import get_engine, init_db
            from frameworks.interfaces import ModelFramework, WhisperFramework, DatabaseFramework, OllamaFramework
            from use_cases.search_service import SearchService
            from use_cases.transcription_service import TranscriptionService
            from use_cases.checkout_service import CheckoutService
            from sqlalchemy.orm import sessionmaker

            engine = get_engine()
            init_db(engine)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Frameworks
            model_fw = ModelFramework()
            
            # Whisper handling (can fail)
            try:
                whisper_fw = WhisperFramework()
            except Exception as e:
                print(f"[CRITICAL] Whisper failed: {e}. Voice features disabled.")
                whisper_fw = None
                
            ollama_fw = OllamaFramework()
            db_fw = DatabaseFramework(
                products_path=PRODUCTS_PATH,
                chroma_path=CHROMA_PATH
            )
            
            # Services
            transcription_service = TranscriptionService(whisper_fw)
            search_service = SearchService(
                transcription_service=transcription_service,
                model_framework=model_fw,
                database_framework=db_fw,
                ollama_framework=ollama_fw
            )
            checkout_service = CheckoutService(db_session_factory=SessionLocal)
            
            _services["search"] = search_service
            _services["checkout"] = checkout_service
            print("DEBUG: Services initialized successfully.")
        except Exception as e:
            import traceback
            print("[CRITICAL] Failed to initialize services:")
            traceback.print_exc()
            raise e
    return _services

# Helper dependencies for routers
from fastapi import Depends
def get_search_service_dep(services: dict = Depends(get_services)):
    return services["search"]

def get_checkout_service_dep(services: dict = Depends(get_services)):
    return services["checkout"]

# Dependency Overrides
app.dependency_overrides[search_router.get_search_service] = get_search_service_dep
app.dependency_overrides[checkout_router.get_checkout_service] = get_checkout_service_dep

# Include Routers
app.include_router(search_router.router)
app.include_router(checkout_router.router)

@app.get("/health")
def health():
    return {"status": "Clean Architecture API running", "services_loaded": len(_services) > 0}

if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else 8000
    print(f"=== Starting Server Process on port {port} ===")
    uvicorn.run(app, host="0.0.0.0", port=port)
