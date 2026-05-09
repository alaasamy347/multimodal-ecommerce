import os
import json
import tempfile
import asyncio
import threading
import traceback
from pathlib import Path
from typing import Optional
from collections import defaultdict
from datetime import datetime

import numpy as np
import faiss
import torch
from PIL import Image
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# ============================================================
# Environment
# ============================================================

_base = Path(__file__).parent
for _f in [_base / ".env.local", _base / ".env"]:
    if _f.exists():
        load_dotenv(dotenv_path=str(_f), override=True)
        print(f"Loaded: {_f.name}")
        break

# ============================================================
# Config
# ============================================================

DATA_DIR         = _base / "data"
IMAGES_DIR       = DATA_DIR / "images"
MODELS_DIR       = DATA_DIR / "pix3d" / "glb"
PRODUCTS_PATH    = DATA_DIR / "clean_products.json"
IMAGE_INDEX_PATH = DATA_DIR / "image_index.faiss"
TEXT_INDEX_PATH  = DATA_DIR / "text_index.faiss"
ID_MAP_PATH      = DATA_DIR / "id_map.npy"
BASE_URL         = os.getenv("BASE_URL", "http://localhost:8000")
DEVICE           = torch.device("cpu")

# Session tracking for evaluation
_session_store = defaultdict(dict)
_session_lock = threading.Lock()

# ============================================================
# State
# ============================================================

_products      = None
_image_index   = None
_text_index    = None
_id_map        = None
_clip_model    = None
_clip_proc     = None
_whisper_model = None

_data_ready    = False
_clip_ready    = False
_whisper_ready = False
_data_error    = None
_clip_error    = None
_whisper_error = None

_data_lock    = threading.Lock()
_clip_lock    = threading.Lock()
_whisper_lock = threading.Lock()
_vlm_lock     = threading.Lock()
_ig_lock      = threading.Lock()

_ig_pipeline  = None
_ig_ready     = False
_ig_error     = None

# ============================================================
# Color Detection & Spell Correction
# ============================================================

_COLORS = {
    "black":    ["black", "noir", "dark"],
    "white":    ["white", "blanc", "cream", "ivory"],
    "red":      ["red", "rouge"],
    "green":    ["green", "vert"],
    "blue":     ["blue", "bleu", "navy"],
    "yellow":   ["yellow", "jaune"],
    "brown":    ["brown", "marron", "tan", "beige"],
    "gray":     ["gray", "grey", "gris"],
    "orange":   ["orange"],
    "pink":     ["pink", "rose"],
    "purple":   ["purple", "violet"],
    "navy":     ["navy", "dark blue"],
    "burgundy": ["burgundy", "wine", "maroon"],
    "teal":     ["teal", "turquoise"],
    "gold":     ["gold", "golden"],
    "silver":   ["silver"],
    "bronze":   ["bronze"],
}

_CORRECTIONS = {
    "wardope": "wardrobe", "wardorbe": "wardrobe", "wardrob": "wardrobe",
    "wardrop": "wardrobe", "wardobe": "wardrobe", "wardrope": "wardrobe",
    "coatch": "couch", "sopha": "sofa", "soaf": "sofa", "couch": "couch",
    "tabel": "table", "tablee": "table", "tabl": "table",
    "cahir": "chair", "chiar": "chair", "chare": "chair", "chair": "chair",
    "bedd": "bed", "beed": "bed", "bed": "bed",
    "shelff": "shelf", "shef": "shelf", "shelf": "shelf",
    "lmap": "lamp", "lapm": "lamp", "lamp": "lamp",
    "cabnet": "cabinet", "cabenit": "cabinet", "cabinet": "cabinet",
    "dresers": "dresser", "draser": "dresser", "dresser": "dresser",
    "otoman": "ottoman", "ottaman": "ottoman", "ottoman": "ottoman",
    "benchh": "bench", "bench": "bench",
    "mirroe": "mirror", "miror": "mirror", "mirror": "mirror",
    "curtan": "curtain", "courtain": "curtain", "curtain": "curtain",
    "desk": "desk", "dsk": "desk",
    "bookcase": "bookcase", "bookshelf": "bookcase", "shelving": "bookcase",
    "armchair": "chair", "lounge": "sofa", "sectional": "sofa",
    "nightstand": "table", "side table": "table", "coffee table": "table",
    "dresser": "dresser", "chest": "dresser", "commode": "dresser",
}

_FURNITURE_KEYWORDS = [
    "sofa", "couch", "chair", "table", "desk", "bed", "shelf", "cabinet",
    "wardrobe", "lamp", "rug", "curtain", "drawer", "bookcase", "stool",
    "bench", "ottoman", "dresser", "mirror", "furniture", "wooden", "leather",
    "black", "white", "brown", "gray", "grey", "red", "blue", "green", "navy",
    "want", "need", "find", "search", "show", "looking", "like", "similar",
    "buy", "modern", "vintage", "small", "large", "dark", "light", "cheap",
    "comfortable", "elegant", "minimalist", "scandinavian", "industrial",
]

def _extract_color(text: str) -> Optional[str]:
    """Extract color from text with fuzzy matching"""
    if not text:
        return None
    words = text.lower().split()
    for word in words:
        for color, variants in _COLORS.items():
            # Exact match or substring match
            if word in variants or any(v in word for v in variants):
                return color
    return None

def _matches_color(product: dict, color: str) -> bool:
    """Check if product matches requested color (General for all colors)"""
    if not color:
        return True
    
    c = color.lower().strip()
    pclr = product.get("baseColour", "").lower().strip()
    pnam = product.get("productDisplayName", "").lower()
    
    # 1. Exact match
    if pclr == c or c in pnam:
        return True
        
    # 2. Synonym/Family match (General for all colors in _COLORS)
    # Check if the requested color is a family name
    if c in _COLORS:
        if pclr in _COLORS[c] or any(v in pnam for v in _COLORS[c]):
            return True
            
    # Check if the product color belongs to the requested color family
    for family, variants in _COLORS.items():
        if c == family or c in variants:
            if pclr == family or pclr in variants:
                return True

    # 3. Handle missing product color
    if not pclr:
        return True # Allow if unknown
        
    return False

def _correct_spelling(text: str) -> str:
    """Spell correction for furniture terms"""
    if not text:
        return text
    
    words = text.lower().split()
    corrected = []
    for word in words:
        corrected.append(_CORRECTIONS.get(word, word))
    return " ".join(corrected)

def _validate_voice_query(transcription: str) -> tuple[bool, Optional[str]]:
    """
    Validate that transcription is a furniture search query, not background noise
    Returns: (is_valid, error_message)
    """
    if not transcription or len(transcription.strip()) < 2:
        return False, "Audio too short — hold mic button longer"
    
    words = transcription.lower().split()
    
    # Check if any furniture keywords present
    has_furniture = sum(1 for w in words if any(f in w for f in _FURNITURE_KEYWORDS))
    
    # Heuristics to detect background noise:
    # 1. Too many words (real searches are short)
    if len(words) > 20:
        # But allow if it has lots of furniture keywords
        if has_furniture < 3:
            return False, f"Heard background noise ({len(words)} words), not a search query. Please speak clearly."
    
    # 2. Very few words AND no furniture keywords
    if len(words) <= 2 and has_furniture == 0:
        return False, f"'{transcription}' is too vague. Try 'black sofa' or 'wooden table'."
    
    # 3. No furniture keywords at all AND longer text
    if has_furniture == 0 and len(words) > 4:
        return False, f"Heard: '{transcription}' — doesn't seem to be about furniture. Try again."
    
    return True, None

def _make_result(product: dict, score: float) -> dict:
    """Convert product + score to API response format"""
    img = product.get("image_path", "")
    glb = product.get("glb_path")
    has3 = product.get("has_3d_model", False)
    
    return {
        "id": product["id"],
        "name": product["productDisplayName"],
        "category": product.get("masterCategory", "Furniture"),
        "subCategory": product.get("subCategory", ""),
        "image": img,
        "color": product.get("baseColour", ""),
        "score": float(max(0.0, min(1.0, score))),
        "has_3d_model": has3,
        "image_url": f"{BASE_URL}/static/images/{img}" if img else "",
        "model_url": f"{BASE_URL}/static/models/{glb}" if (has3 and glb) else None,
    }

# ============================================================
# App
# ============================================================

app = FastAPI(title="Multimodal Furniture Search", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class _CORSStatic(StaticFiles):
    async def get_response(self, path, scope):
        r = await super().get_response(path, scope)
        r.headers["Access-Control-Allow-Origin"] = "*"
        r.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        return r


if IMAGES_DIR.exists():
    app.mount("/static/images", _CORSStatic(directory=str(IMAGES_DIR)), name="images")
if MODELS_DIR.exists():
    app.mount("/static/models", _CORSStatic(directory=str(MODELS_DIR)), name="models")


@app.on_event("startup")
async def startup():
    print("\n=== Server ready: http://localhost:8000 ===\n")

# ============================================================
# Lazy loaders
# ============================================================

def _ensure_data():
    """Load product data and FAISS indexes"""
    global _products, _image_index, _text_index, _id_map, _data_ready, _data_error
    with _data_lock:
        if _data_ready:
            return True
        try:
            print("[DATA] Loading products and indexes...")
            with open(PRODUCTS_PATH, encoding="utf-8") as f:
                _products = json.load(f)
            _image_index = faiss.read_index(str(IMAGE_INDEX_PATH))
            _text_index = faiss.read_index(str(TEXT_INDEX_PATH))
            _id_map = np.load(str(ID_MAP_PATH))
            _data_ready = True
            print(f"[DATA] Ready — {len(_products)} products indexed")
            return True
        except Exception as e:
            _data_error = str(e)
            print(f"[DATA] ERROR: {e}")
            traceback.print_exc()
            return False


def _ensure_clip():
    """Load CLIP model"""
    global _clip_model, _clip_proc, _clip_ready, _clip_error
    with _clip_lock:
        if _clip_ready:
            return True
        try:
            print("[CLIP] Loading model (~30s first time)...")
            from transformers import CLIPModel, CLIPProcessor
            _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            _clip_model.to(DEVICE).eval()
            _clip_proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            _clip_ready = True
            print("[CLIP] Ready")
            return True
        except Exception as e:
            _clip_error = str(e)
            print(f"[CLIP] ERROR: {e}")
            traceback.print_exc()
            return False


def _ensure_whisper():
    """Load Whisper ASR model"""
    global _whisper_model, _whisper_ready, _whisper_error
    with _whisper_lock:
        if _whisper_ready:
            return True
        try:
            print("[WHISPER] Loading openai-whisper tiny...")
            import whisper
            _whisper_model = whisper.load_model("tiny")
            _whisper_ready = True
            print("[WHISPER] Ready")
            return True
        except ImportError:
            _whisper_error = "openai-whisper not installed. Run: pip install openai-whisper"
            print(f"[WHISPER] {_whisper_error}")
            return False
        except Exception as e:
            _whisper_error = str(e)
            print(f"[WHISPER] ERROR: {e}")
            traceback.print_exc()
            return False

def _ensure_ig():
    global _ig_ready
    _ig_ready = True
    return True

@app.post("/generate_image")
async def generate_image(prompt: str = Form(...)):
    """Generate image using Free Pollinations API (No 7GB download needed)"""
    loop = asyncio.get_event_loop()
    try:
        import urllib.request
        import urllib.parse
        import os
        
        def do_gen(p: str):
            encoded_prompt = urllib.parse.quote(p)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            out_name = f"gen_{os.urandom(4).hex()}.jpg"
            out_path = IMAGES_DIR / out_name
            os.makedirs(IMAGES_DIR, exist_ok=True)
            
            with urllib.request.urlopen(req) as response, open(out_path, 'wb') as out_file:
                out_file.write(response.read())
                
            return out_name
            
        img_name = await loop.run_in_executor(None, do_gen, prompt)
        return {"image_url": f"{BASE_URL}/static/images/{img_name}", "prompt": prompt}
    except Exception as e:
        print(f"[IG] Generation error: {e}")
        raise HTTPException(500, detail=str(e))

def _process_with_vlm(image_paths: list, text_query: str) -> dict:
    """Send image and text to local Ollama (llava) to extract semantic filters."""
    import requests
    import base64
    
    url = "http://localhost:11434/api/generate"
    images_b64 = []
    
    for img_path in image_paths:
        with open(img_path, "rb") as f:
            images_b64.append(base64.b64encode(f.read()).decode("utf-8"))
            
    prompt = f"Analyze these images. the user asks: '{text_query}'. Focus on furniture. Reply in strict JSON format: {{\"color\": \"predominant color\", \"category\": \"furniture category\", \"style\": \"decor style\", \"reasoning\": \"brief explanation\"}}. Output only raw JSON."
    
    try:
        res = requests.post(url, json={
            "model": "llava",
            "prompt": prompt,
            "images": images_b64,
            "stream": False,
            "format": "json"
        }, timeout=30)
        
        if res.status_code == 200:
            return res.json().get("response", "{}")
    except Exception as e:
        print(f"[VLM] Error: {e}")
    
    return "{}"

# ============================================================
# Search implementation
# ============================================================

def _do_search(
    query: str,
    img_paths: Optional[list],
    color: Optional[str],
    top_k: int,
    session_id: str,
    category: Optional[str] = None,
) -> tuple[list, dict]:
    """
    Execute multimodal search
    Returns: (results, metadata)
    """
    metadata = {
        "query": query,
        "has_image": bool(img_paths),
        "image_count": len(img_paths) if img_paths else 0,
        "color_filter": color,
        "modalities": [],
        "embedding_sources": [],
    }
    
    vecs = []
    
    # TEXT ENCODING
    if query.strip():
        corrected = _correct_spelling(query)
        metadata["corrected_query"] = corrected if corrected != query else None
        
        inp = _clip_proc(
            text=[corrected],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=77
        ).to(DEVICE)
        
        with torch.no_grad():
            v = _clip_model.get_text_features(**inp).cpu().numpy().astype("float32")
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        vecs.append(v[0])
        metadata["modalities"].append("text")
        metadata["embedding_sources"].append("CLIP-Text")
    
    # IMAGE ENCODING
    if img_paths:
        for img_path in img_paths:
            try:
                img = Image.open(img_path).convert("RGB")
                inp = _clip_proc(images=img, return_tensors="pt").to(DEVICE)
                with torch.no_grad():
                    v = _clip_model.get_image_features(**inp).cpu().numpy().astype("float32")
                v /= np.linalg.norm(v, axis=1, keepdims=True)
                vecs.append(v[0])
                if "image" not in metadata["modalities"]:
                    metadata["modalities"].append("image")
                    metadata["embedding_sources"].append("CLIP-Vision")
            except Exception as e:
                print(f"[IMAGE] Processing error: {e}")
                metadata.setdefault("image_errors", []).append(str(e))
    
    if not vecs:
        return [], metadata
    
    # COMBINE EMBEDDINGS (Weighted)
    if len(vecs) > 1 and query.strip():
        # If the query is long/complex, give image more weight to preserve visual style
        # If it's short (like "red sofa"), text gets more weight to enforce the constraint
        text_weight = 0.5 if len(query.split()) > 3 else 0.7
        img_weight = 1.0 - text_weight
        
        text_vec = vecs[0]
        img_vecs = vecs[1:]
        img_avg = np.mean(img_vecs, axis=0)
        combined = (text_weight * text_vec + img_weight * img_avg).reshape(1, -1).astype("float32")
    else:
        combined = np.mean(vecs, axis=0, keepdims=True).astype("float32")
    
    combined /= np.linalg.norm(combined, axis=1, keepdims=True)
    metadata["combined_modalities"] = "+".join(metadata["modalities"])
    
    # RETRIEVE
    # Use image index if image provided (for visual similarity), otherwise text index
    index = _image_index if img_paths else _text_index
    dists, idxs = index.search(combined, top_k * 6)
    
    results = []
    for dist, idx in zip(dists[0], idxs[0]):
        if idx < 0:
            continue
        product = _products[int(_id_map[int(idx)])]
        
        # COLOR FILTER (Soft)
        color_match = _matches_color(product, color) if color else True
        final_score = float(dist)
        
        # If color doesn't match, apply penalty but don't skip yet
        # This allows showing 'similar' items if exact colors aren't found
        if not color_match:
            final_score -= 0.15
        
        # CATEGORY BOOST: 
        # 1. Direct mention in text
        # 2. Detected by VLM from image
        target_category = (category or "").lower()
        prod_cat = (product.get("subCategory") or "").lower()
        
        if target_category and target_category in prod_cat:
            final_score += 0.2 # Significant boost for matching the VLM's identified category
        elif "sofa" in query.lower() and prod_cat == "sofa":
            final_score += 0.1
        elif "bed" in query.lower() and prod_cat == "bed":
            final_score += 0.1
        elif "table" in query.lower() and prod_cat == "table":
            final_score += 0.1
            
        results.append({
            **_make_result(product, final_score),
            "embedding_distance": float(dist),
            "color_match": color_match,
            "category_boosted": bool(target_category and target_category in prod_cat)
        })
        
        if len(results) >= top_k * 2: # Get more results for sorting
            break
    
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    
    # LOG SESSION
    with _session_lock:
        if session_id not in _session_store:
            _session_store[session_id] = {
                "timestamp": datetime.now().isoformat(),
                "searches": [],
            }
        _session_store[session_id]["searches"].append({
            "query": query,
            "modalities": metadata["modalities"],
            "color_filter": color,
            "results_count": len(results_sorted),
            "top_score": results_sorted[0]["score"] if results_sorted else 0.0,
            "timestamp": datetime.now().isoformat(),
        })
    
    metadata["total_results"] = len(results_sorted)
    if results_sorted:
        metadata["top_match_score"] = results_sorted[0]["score"]
    
    return results_sorted, metadata


def _do_transcribe(path: str) -> tuple[str, Optional[str]]:
    """
    Transcribe WAV file
    Returns: (text, error_message)
    """
    if os.path.getsize(path) < 200:
        return "", "Audio too short"
    
    if not _whisper_model:
        return "", "Whisper not available"
    
    try:
        import wave
        import struct
        
        # Read WAV
        with wave.open(path, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)
        
        # Decode to float32
        if sampwidth == 2:
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            samples = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
        
        # Mix stereo to mono
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)
        
        # Resample if needed
        if framerate != 16000:
            factor = 16000 / framerate
            new_len = int(len(samples) * factor)
            indices = np.linspace(0, len(samples) - 1, new_len)
            samples = np.interp(indices, np.arange(len(samples)), samples).astype(np.float32)
        
        # Transcribe
        result = _whisper_model.transcribe(samples, language="en", fp16=False)
        text = result["text"].strip()
        print(f"[WHISPER] Transcribed: '{text}'")
        
        return text, None
        
    except Exception as e:
        print(f"[WHISPER] Error: {e}")
        traceback.print_exc()
        return "", str(e)

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
def root():
    """Root endpoint with system status"""
    return {
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "data_ready": _data_ready,
            "clip_ready": _clip_ready,
            "whisper_ready": _whisper_ready,
            "errors": {
                "data": _data_error,
                "clip": _clip_error,
                "whisper": _whisper_error,
            },
            "products_indexed": len(_products) if _products else 0,
            "active_sessions": len(_session_store),
        },
    }

import uuid
@app.post("/checkout/cart/add/{product_id}")
async def add_to_cart(product_id: int, session_id: str):
    """Mock cart sync endpoint"""
    print(f"[CART] Session {session_id} added product {product_id}")
    return {"status": "success", "session_id": session_id}

@app.post("/checkout/order")
async def checkout_order(session_id: str):
    """Mock checkout order generator so the frontend can complete purchases"""
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    print(f"[CHECKOUT] Session {session_id} completed order {order_id}")
    return {"order_id": order_id, "status": "success"}


@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "healthy" if (_data_ready and _clip_ready) else "loading",
        "data_ready": _data_ready,
        "clip_ready": _clip_ready,
        "whisper_ready": _whisper_ready,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Fetch single product by ID"""
    loop = asyncio.get_event_loop()
    
    if not _data_ready:
        await loop.run_in_executor(None, _ensure_data)
    if not _data_ready:
        raise HTTPException(503, detail=f"Data error: {_data_error}")
    
    if product_id < 0 or product_id >= len(_products):
        raise HTTPException(404, detail="Product not found")
    
    p = _products[product_id]
    glb = p.get("glb_path")
    has3 = p.get("has_3d_model", False)
    img = p.get("image_path", "")
    murl = f"{BASE_URL}/static/models/{glb}" if (has3 and glb) else None
    
    return {
        "id": p["id"],
        "name": p["productDisplayName"],
        "category": p.get("masterCategory", "Furniture"),
        "subCategory": p.get("subCategory", ""),
        "image": img,
        "color": p.get("baseColour", ""),
        "has_3d_model": has3,
        "glb_path": glb or "",
        "image_url": f"{BASE_URL}/static/images/{img}" if img else "",
        "model_url": murl,
        "model_exists": (MODELS_DIR / glb).exists() if murl else False,
    }


@app.post("/generate_image")
async def generate_image(prompt: str = Form(...)):
    """Generate image based on prompt using SD Turbo"""
    loop = asyncio.get_event_loop()
    
    if not _ig_ready:
        print("[IG] Loading for first generation request...")
        await loop.run_in_executor(None, _ensure_ig)
        
    if not _ig_ready:
        raise HTTPException(500, detail=_ig_error or "Image Generation unavailable")
        
    try:
        def do_gen(p: str):
            image = _ig_pipeline(prompt=p, num_inference_steps=1, guidance_scale=0.0).images[0]
            out_name = f"gen_{os.urandom(4).hex()}.jpg"
            out_path = IMAGES_DIR / out_name
            os.makedirs(IMAGES_DIR, exist_ok=True)
            image.save(out_path)
            return out_name
            
        img_name = await loop.run_in_executor(None, do_gen, prompt)
        return {"image_url": f"{BASE_URL}/static/images/{img_name}", "prompt": prompt}
    except Exception as e:
        print(f"[IG] Generation error: {e}")
        raise HTTPException(500, detail=str(e))

@app.post("/search/intelligent")
async def search(
    query: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None),
    image: Optional[list[UploadFile]] = File(None),
    audio: Optional[UploadFile] = File(None),
    top_k: int = Form(10),
    session_id: str = Form("default"),
):
    """
    Multimodal search endpoint
    Accepts: text query, image upload, audio upload
    Returns: ranked list of products with metadata
    """
    loop = asyncio.get_event_loop()
    
    # Ensure data loaded
    if not _data_ready:
        await loop.run_in_executor(None, _ensure_data)
    if not _data_ready:
        raise HTTPException(503, detail=f"Data error: {_data_error}")
    
    # Ensure CLIP loaded
    if not _clip_ready:
        print("[CLIP] First request — loading now (~30s)...")
        ok = await loop.run_in_executor(None, _ensure_clip)
        if not ok:
            raise HTTPException(500, detail=f"CLIP failed: {_clip_error}")
    
    # Process inputs
    typed_query = (query or "").strip()
    voice_query = ""
    voice_error = None
    tmp_audio = None
    tmp_img = None
    
    # VOICE PROCESSING
    if audio:
        try:
            data = await audio.read()
            print(f"[VOICE] Received {len(data)} bytes")
            
            if not _whisper_ready:
                print("[WHISPER] Loading for first voice request...")
                await loop.run_in_executor(None, _ensure_whisper)
            
            if not _whisper_ready:
                voice_error = _whisper_error or "Whisper unavailable"
            elif len(data) < 200:
                voice_error = "Audio too short — hold mic button longer"
            else:
                # Save and transcribe
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(data)
                    tmp_audio = f.name
                
                voice_query, trans_error = await loop.run_in_executor(
                    None, _do_transcribe, tmp_audio
                )
                
                if trans_error:
                    voice_error = f"Transcription failed: {trans_error}"
                elif voice_query:
                    # VALIDATE voice query
                    is_valid, validation_error = _validate_voice_query(voice_query)
                    if not is_valid:
                        voice_error = validation_error
                        voice_query = ""
                    else:
                        print(f"[VOICE] Accepted: '{voice_query}'")
                else:
                    voice_error = "Could not understand audio"
        
        except Exception as e:
            voice_error = str(e)
            print(f"[VOICE] Error: {e}")
            traceback.print_exc()
        
        finally:
            if tmp_audio and os.path.exists(tmp_audio):
                os.remove(tmp_audio)
    
    # MERGE QUERIES
    color_filter = _extract_color(voice_query) or _extract_color(typed_query)
    final_query = (
        f"{voice_query} {typed_query}".strip()
        if voice_query and typed_query
        else voice_query or typed_query
    )
    
    print(f"[SEARCH] typed='{typed_query}' voice='{voice_query}' final='{final_query}' color={color_filter}")
    
    # IMAGE PROCESSING
    upload_files = []
    if file:
        upload_files.append(file)
    if image:
        if isinstance(image, list):
            upload_files.extend(image)
        else:
            upload_files.append(image)
            
    tmp_imgs = []
    for upload_file in upload_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(await upload_file.read())
            tmp_imgs.append(f.name)
    
    # CHECK INPUT
    if not final_query and not tmp_imgs:
        return {
            "query": "",
            "interpreted_query": "",
            "typed_query": typed_query,
            "voice_query": voice_query,
            "voice_error": voice_error,
            "accurate_results": [],
            "related_results": [],
            "total_results": 0,
            "color_filter": None,
            "search_mode": "none",
            "message": "Please provide text, image, or voice input",
        }
    
    # VLM REASONING (if complex query over threshold or requested)
    vlm_result = {}
    if final_query and tmp_imgs and len(final_query.split()) >= 3:
        try:
            print("[VLM] Routing to Visual Language Model (llava)...")
            import string
            vlm_resp = await loop.run_in_executor(None, _process_with_vlm, tmp_imgs, final_query)
            try:
                import json
                vlm_result = dict(json.loads(vlm_resp))
                if "color" in vlm_result and not color_filter:
                    color_filter = vlm_result["color"].lower()
                print(f"[VLM] Parsed Result: {vlm_result}")
            except:
                pass
        except Exception as e:
             print(f"[VLM] Processing failed: {e}")

    # EXECUTE SEARCH
    try:
        results_sorted, metadata = await loop.run_in_executor(
            None,
            _do_search,
            final_query,
            tmp_imgs,
            color_filter,
            top_k,
            session_id,
            vlm_result.get("category"),
        )
        if vlm_result:
            metadata["vlm_reasoning"] = vlm_result
    except Exception as e:
        print(f"[SEARCH] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, detail=f"Search failed: {e}")
    
    finally:
        for timg in tmp_imgs:
            if os.path.exists(timg):
                os.remove(timg)
    
    # BUILD RESPONSE
    modes = []
    if typed_query:
        modes.append("text")
    if tmp_imgs:
        modes.append("image")
    if voice_query:
        modes.append("voice")
    
    search_mode = " + ".join(modes) if modes else "unknown"
    
    # BUILD AI SUMMARY
    ai_summary = None
    if vlm_result and isinstance(vlm_result, dict):
        reasoning = vlm_result.get("reasoning")
        cat = vlm_result.get("category")
        col = vlm_result.get("color")
        
        if reasoning and str(reasoning).lower() != "undefined":
            ai_summary = reasoning
        elif cat:
            ai_summary = f"I've identified the item in your image as a {col or ''} {cat}. Searching for similar items..."

    return {
        "query": final_query,
        "interpreted_query": final_query,
        "typed_query": typed_query,
        "voice_query": voice_query,
        "voice_error": voice_error,
        "corrected_query": metadata.get("corrected_query"),
        "accurate_results": results_sorted[:top_k],
        "related_results": results_sorted[top_k:top_k*2],
        "total_results": len(results_sorted),
        "color_filter": color_filter,
        "search_mode": search_mode,
        "ai_summary": ai_summary,
        "metadata": metadata,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
    }

def search_with_color_priority(query: str, image_path: Optional[str], top_k: int) -> list:
    # Step 1: Extract requested color from text
    requested_color = _extract_color(query)
    
    # Step 2: Get embeddings
    text_emb = _encode_text(query)
    
    if image_path:
        image_emb = _encode_image(image_path)
        # Weight: 70% text (respects color), 30% image (respects shape)
        combined = (text_emb * 0.7) + (image_emb * 0.3)
    else:
        combined = text_emb
    
    # Step 3: Search
    distances, indices = _image_index.search(combined.reshape(1, -1), top_k * 4)
    
    # Step 4: Filter by color if requested
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        product = _products[int(_id_map[idx])]
        
        # Prioritize matching colors
        if requested_color:
            if _matches_color(product, requested_color):
                results.append((dist, product, True))  # Color match
            else:
                results.append((dist, product, False))  # No color match
        else:
            results.append((dist, product, None))
    
    # Sort: color matches first, then by distance
    results.sort(key=lambda x: (x[2] is False, -x[0]))  # False (no match) last
    
    return [r[1] for r in results[:top_k]]

    
@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve session data for evaluation"""
    with _session_lock:
        if session_id not in _session_store:
            raise HTTPException(404, detail="Session not found")
        return _session_store[session_id]


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    with _session_lock:
        return {
            "active_sessions": len(_session_store),
            "sessions": list(_session_store.keys()),
            "total_searches": sum(
                len(s.get("searches", [])) for s in _session_store.values()
            ),
        }


@app.post("/sessions/export")
async def export_sessions():
    """Export all session data for analysis"""
    with _session_lock:
        return {
            "exported_at": datetime.now().isoformat(),
            "total_sessions": len(_session_store),
            "sessions": dict(_session_store),
        }


if __name__ == "__main__":
    import uvicorn
    print("\nStarting — http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, workers=1)