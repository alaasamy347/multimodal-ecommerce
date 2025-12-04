# import os
# import json
# import tempfile
# from pathlib import Path
# from typing import Optional, List, Dict

# import uvicorn
# import faiss
# import numpy as np
# import torch
# import requests
# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from transformers import CLIPProcessor, CLIPModel
# from PIL import Image
# from dotenv import load_dotenv

# # ============================
# # ENV + CONFIG
# # ============================
# load_dotenv(".env.local")
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# DATA_IMAGES_DIR = "data/images"
# CLEAN_PRODUCTS_PATH = "data/clean_products.json"
# IMAGE_INDEX_PATH = "data/image_index.faiss"
# TEXT_INDEX_PATH = "data/text_index.faiss"
# ID_MAP_PATH = "data/id_map.npy"

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# # Gemini setup
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
#     if GEMINI_API_KEY:
#         genai.configure(api_key=GEMINI_API_KEY)
#         print("✅ Gemini configured")
#     else:
#         print("⚠️ Gemini key missing")
# except ImportError:
#     GEMINI_AVAILABLE = False
#     print("⚠️ Gemini library not installed")

# # ============================
# # FASTAPI + MODELS
# # ============================
# app = FastAPI(title="Free LLM Multimodal Search (Gemini + Groq)")
# app.mount("/static", StaticFiles(directory=DATA_IMAGES_DIR), name="static")
# app.mount("/models", StaticFiles(directory="data/models"), name="models")

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# torch.set_grad_enabled(False)

# # ============================
# # LOAD DATA
# # ============================
# print("📦 Loading FAISS indexes and metadata...")
# image_index = faiss.read_index(IMAGE_INDEX_PATH)
# text_index = faiss.read_index(TEXT_INDEX_PATH)
# id_map = np.load(ID_MAP_PATH)
# with open(CLEAN_PRODUCTS_PATH, "r", encoding="utf-8") as f:
#     products = {int(p["id"]): p for p in json.load(f)}

# CATEGORIES = list(set(p.get("subCategory", "") for p in products.values() if p.get("subCategory")))

# # ============================
# # CLIP MODEL
# # ============================
# clip_model = None
# clip_processor = None

# def get_clip():
#     global clip_model, clip_processor
#     if clip_model is None:
#         print("🔠 Loading CLIP model...")
#         clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
#         clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
#         clip_model.eval()
#     return clip_model, clip_processor

# # ============================
# # GROQ + GEMINI HELPERS
# # ============================
# def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
#     if not GROQ_API_KEY:
#         return "⚠️ Groq API key not set"
#     try:
#         res = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
#             json={
#                 "model": "llama-3.3-70b-versatile",
#                 "messages": messages,
#                 "temperature": temperature,
#                 "max_tokens": 800,
#             },
#             timeout=30,
#         )
#         if res.status_code == 200:
#             return res.json()["choices"][0]["message"]["content"]
#         print(f"❌ Groq error: {res.status_code}")
#         return ""
#     except Exception as e:
#         print(f"❌ Groq failed: {e}")
#         return ""

# def analyze_image_gemini(image_path: str) -> str:
#     if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
#         return ""
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         img = Image.open(image_path)
#         prompt = """Describe this furniture image in detail:
# - Furniture type (chair, table, etc.)
# - Color and material
# - Style (modern, rustic, etc.)
# Keep it short."""
#         response = model.generate_content([prompt, img])
#         return response.text.strip()
#     except Exception as e:
#         print(f"⚠️ Gemini image analysis failed: {e}")
#         return ""

# # ============================
# # SEARCH UTILS
# # ============================
# def cosine_similarity_to_percentage(distance):
#     return max(0.0, 1.0 - (distance ** 2) / 2.0)

# def get_top_k_results(embeddings, index, k=10, category_filter=None):
#     distances, indices = index.search(embeddings, k * 5)
#     results = []
#     for dist, idx in zip(distances[0], indices[0]):
#         if idx < 0:
#             continue
#         product_id = int(id_map[int(idx)])
#         p = products.get(product_id, {})
#         if not p:
#             continue
#         if category_filter and p.get("subCategory") != category_filter:
#             continue
#         results.append({
#             "id": product_id,
#             "name": p.get("productDisplayName"),
#             "category": p.get("masterCategory"),
#             "subCategory": p.get("subCategory"),
#             "image": p.get("image_path"),
#             "score": float(cosine_similarity_to_percentage(dist)),
#         })
#     return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

# # ============================
# # MAIN SEARCH ENDPOINT
# # ============================
# # @app.post("/search/intelligent")
# # async def intelligent_search(
# #     file: UploadFile = File(None),
# #     query: str = Form(""),
# #     top_k: int = Form(10),
# #     session_id: str = Form("default"),
# # ):
# #     """AI-powered multimodal search"""
# #     image_description = None

# #     # Image understanding
# #     if file and GEMINI_AVAILABLE and GEMINI_API_KEY:
# #         try:
# #             tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
# #             tmp.write(await file.read())
# #             tmp.close()
# #             image_description = analyze_image_gemini(tmp.name)
# #             os.remove(tmp.name)
# #             print(f"🖼️ Gemini detected: {image_description}")
# #         except Exception as e:
# #             print(f"⚠️ Image analysis error: {e}")

# #     # Expand query for CLIP
# #     def expand_query(q):
# #         messages = [
# #             {"role": "system", "content": "You expand product search queries to emphasize key visual words like color, material, and style."},
# #             {"role": "user", "content": q},
# #         ]
# #         r = call_groq(messages, temperature=0.4)
# #         return r.strip() if r else q

# #     expanded_query = expand_query(query)
# #     final_query = expanded_query + (f". Similar to: {image_description}" if image_description else "")
# #     print(f"🧠 Final interpreted query: {final_query}")

# #     # Encode with CLIP
# #     clip_model, clip_processor = get_clip()
# #     with torch.no_grad():
# #         inputs = clip_processor(text=[final_query], return_tensors="pt").to(device)
# #         txt_emb = clip_model.get_text_features(**inputs)
# #     txt_emb = txt_emb.cpu().numpy()
# #     txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)

# #     # Search results
# #     results = get_top_k_results(txt_emb, text_index, k=top_k * 3)

# #     # Split results
# #     accurate_results = [r for r in results if r["score"] >= 0.88]
# #     related_results = [r for r in results if 0.7 <= r["score"] < 0.88]

# #     if not accurate_results:
# #         accurate_results = related_results[:5]
# #         related_results = related_results[5:10]

# #     # Natural explanation
# #     messages = [
# #         {"role": "system", "content": "You are a friendly shopping assistant."},
# #         {"role": "user", "content": f"""
# # User searched for: "{query}".
# # Expanded search: "{final_query}".
# # Found {len(accurate_results)} strong matches and {len(related_results)} related items.

# # Write a short conversational summary (2–3 sentences). 
# # If few matches exist, suggest similar options or style variations.
# # Avoid technical tone.
# # """},
# #     ]
# #     natural_response = call_groq(messages, temperature=0.7)

# #     return {
# #         "query": query,
# #         "interpreted_query": final_query,
# #         "ai_summary": natural_response,
# #         "accurate_results": accurate_results[:top_k],
# #         "related_results": related_results[:top_k],
# #         "llm_status": {
# #             "vision": "gemini" if image_description else "none",
# #             "reasoning": "groq" if GROQ_API_KEY else "none",
# #         },
# #     }

# @app.post("/search/intelligent")
# async def intelligent_search(
#     query: str = Form(""),
#     image: UploadFile = File(None),
#     audio: UploadFile = File(None),
#     top_k: int = Form(10),
#     session_id: str = Form("default"),
# ):
#     """
#     Multimodal Search:
#     - text (query)
#     - image (UploadFile)
#     - audio (UploadFile)
#     Any combination is allowed.
#     """

#     final_query_vector = None
#     modality_vectors = []

#     # ---------- TEXT ----------
#     if query.strip():
#         text_vec = text_model.encode([query])[0]
#         modality_vectors.append(text_vec)

#     # ---------- IMAGE ----------
#     if image:
#         image_bytes = await image.read()
#         image_vec = image_model.extract_features(image_bytes)
#         modality_vectors.append(image_vec)

#     # ---------- AUDIO ----------
#     if audio:
#         audio_bytes = await audio.read()
#         # Convert audio → text (speech-to-text)
#         transcript = audio_to_text(audio_bytes)  # You'll implement this
#         audio_vec = text_model.encode([transcript])[0]
#         modality_vectors.append(audio_vec)

#     # ---------- COMBINE ----------
#     if not modality_vectors:
#         return JSONResponse({"error": "No input provided"}, status_code=400)

#     final_query_vector = np.mean(modality_vectors, axis=0).astype("float32")

#     # ---------- FAISS SEARCH ----------
#     distances, indices = index.search(
#         np.array([final_query_vector]).astype("float32"),
#         top_k
#     )

#     results = [
#         {"id": int(i), "score": float(d)}
#         for i, d in zip(indices[0], distances[0])
#     ]

#     return {"results": results}

# # ============================
# # MISC ROUTES
# # ============================
# @app.get("/")
# def root():
#     return {"message": "LLM Multimodal Search API Ready", "groq": bool(GROQ_API_KEY), "gemini": GEMINI_AVAILABLE}

# @app.post("/conversation/reset")
# async def reset_conversation(session_id: str = Form("default")):
#     return {"message": f"Conversation {session_id} reset"}

# @app.get("/products/{product_id}/ar-info")
# async def get_ar_info(product_id: int):
#     product = products.get(product_id)
#     if not product:
#         return JSONResponse(status_code=404, content={"error": "Product not found"})
#     model_path = Path(f"data/models/{product_id}.glb")
#     base_url = "http://localhost:8000"
#     return {
#         "product_id": product_id,
#         "name": product.get("productDisplayName"),
#         "model_url": f"{base_url}/models/{product_id}.glb" if model_path.exists() else None,
#         "poster_url": f"{base_url}/static/{product.get('image_path')}",
#         "ar_available": model_path.exists(),
#     }

# # ============================
# # CORS
# # ============================
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# if __name__ == "__main__":
#     print("=" * 60)
#     print("🚀 FREE MULTIMODAL SEARCH SERVER")
#     print("=" * 60)
#     print(f"Gemini (vision): {'✅' if GEMINI_AVAILABLE and GEMINI_API_KEY else '❌'}")
#     print(f"Groq (reasoning): {'✅' if GROQ_API_KEY else '❌'}")
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)



import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

import uvicorn
import faiss
import numpy as np
import torch
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from dotenv import load_dotenv

# ============================
# ENV + CONFIG
# ============================
load_dotenv(".env.local")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

DATA_IMAGES_DIR = "data/images"
CLEAN_PRODUCTS_PATH = "data/clean_products.json"
IMAGE_INDEX_PATH = "data/image_index.faiss"
TEXT_INDEX_PATH = "data/text_index.faiss"
ID_MAP_PATH = "data/id_map.npy"
MODELS_DIR = "data/models"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # For Whisper (audio transcription)

# Gemini setup
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini configured")
    else:
        print("⚠️ Gemini key missing")
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini library not installed")

# ============================
# FASTAPI + MODELS
# ============================
app = FastAPI(title="Multimodal Search with AR & Voice")
app.mount("/static", StaticFiles(directory=DATA_IMAGES_DIR), name="static")
app.mount("/models", StaticFiles(directory=MODELS_DIR), name="models")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

# ============================
# SAFE LOADERS
# ============================
def safe_load_faiss(path):
    if os.path.exists(path):
        return faiss.read_index(path)
    print(f"⚠️ FAISS not found: {path}")
    return None

def safe_load_npy(path):
    if os.path.exists(path):
        return np.load(path)
    print(f"⚠️ NPY not found: {path}")
    return None

def safe_load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {int(p["id"]): p for p in json.load(f)}
    print(f"⚠️ JSON not found: {path}")
    return {}

print("📦 Loading FAISS indexes and metadata...")
image_index = safe_load_faiss(IMAGE_INDEX_PATH)
text_index = safe_load_faiss(TEXT_INDEX_PATH)
id_map = safe_load_npy(ID_MAP_PATH)
products = safe_load_json(CLEAN_PRODUCTS_PATH)

CATEGORIES = list(set(p.get("subCategory", "") for p in products.values() if p.get("subCategory")))
print(f"✅ Loaded {len(products)} products")

# ============================
# CLIP MODEL
# ============================
clip_model = None
clip_processor = None

def get_clip():
    global clip_model, clip_processor
    if clip_model is None:
        print("🔠 Loading CLIP model...")
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        clip_model.eval()
    return clip_model, clip_processor

# ============================
# IMAGE COLOR DETECTION
# ============================
# ============================
# COLOR DETECTION
# ============================
COMMON_COLORS = [
    "red", "blue", "green", "yellow", "black", "white", "brown", "grey", "gray",
    "pink", "purple", "orange", "beige", "navy", "burgundy", "maroon", "tan"
]

def detect_color_from_image(image_path: str) -> Optional[str]:
    """Detect dominant color from uploaded image"""
    try:
        from PIL import Image
        import numpy as np
        
        img = Image.open(image_path).convert('RGB')
        img = img.resize((100, 100))  # Downsample for speed
        
        # Get all pixels
        pixels = np.array(img).reshape(-1, 3)
        
        # Calculate average color
        avg_color = np.mean(pixels, axis=0)
        
        # Map to color name
        def rgb_to_color_name(rgb):
            r, g, b = rgb
            
            # Color detection logic
            if max(r, g, b) < 80:
                return "black"
            if min(r, g, b) > 200:
                return "white"
            
            # Find dominant channel
            if r > g + 30 and r > b + 30:
                if r > 180 and g < 100:
                    return "red"
                elif r > 150 and g > 100:
                    return "orange"
                else:
                    return "pink"
            elif g > r + 30 and g > b + 30:
                return "green"
            elif b > r + 30 and b > g + 30:
                return "blue"
            elif r > 150 and g > 120 and b < 100:
                return "orange"
            elif r > 120 and g > 100 and b > 120:
                return "purple"
            elif abs(r - g) < 30 and abs(g - b) < 30:
                if r > 150:
                    return "white"
                elif r > 100:
                    return "grey"
                else:
                    return "black"
            elif r > 100 and g > 80 and b < 80:
                return "brown"
            
            return None
        
        color_name = rgb_to_color_name(avg_color)
        print(f"🎨 Image color detected: {color_name} (RGB: {avg_color})")
        return color_name
        
    except Exception as e:
        print(f"⚠️ Color detection failed: {e}")
        return None

def extract_color_from_query(query: str) -> Optional[str]:
    query_lower = query.lower()
    for color in COMMON_COLORS:
        if color in query_lower:
            return color
    return None

def product_matches_color(product: Dict, color: str) -> bool:
    """Check if product matches the requested color"""
    if not color:
        return True
    
    name = product.get("productDisplayName", "").lower()
    prod_color = product.get("color", "").lower()
    
    # Direct match
    if color in name or color in prod_color:
        return True
    
    # Color variations and synonyms
    color_groups = {
        "red": ["red", "crimson", "burgundy", "maroon", "scarlet", "ruby"],
        "blue": ["blue", "navy", "azure", "cobalt", "indigo", "sapphire"],
        "green": ["green", "olive", "emerald", "lime", "forest", "mint"],
        "yellow": ["yellow", "gold", "golden", "amber", "cream"],
        "black": ["black", "ebony", "charcoal", "dark"],
        "white": ["white", "ivory", "cream", "off-white", "beige"],
        "brown": ["brown", "tan", "beige", "chocolate", "mocha", "walnut", "oak"],
        "grey": ["grey", "gray", "silver", "slate"],
        "pink": ["pink", "rose", "blush", "magenta", "coral"],
        "purple": ["purple", "violet", "lavender", "plum", "mauve"],
        "orange": ["orange", "coral", "peach", "tangerine"],
    }
    
    # Check if product color matches any variation
    color_variations = color_groups.get(color, [color])
    for variation in color_variations:
        if variation in name or variation in prod_color:
            return True
    
    return False

# ============================
# LLM HELPERS
# ============================
def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
    if not GROQ_API_KEY:
        return ""
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 400,
            },
            timeout=20,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ Groq error: {e}")
    return ""

def analyze_image_gemini(image_path: str) -> str:
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return ""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = Image.open(image_path)
        prompt = "Describe this furniture in 5-10 words: type, color, material."
        response = model.generate_content([prompt, img])
        return response.text.strip()[:100]
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
    return ""

# ============================
# AUDIO TRANSCRIPTION (WHISPER)
# ============================
def transcribe_audio_whisper(audio_path: str) -> str:
    """
    Transcribe audio to text using OpenAI Whisper API
    """
    if not OPENAI_API_KEY:
        print("⚠️ OpenAI API key not set - audio transcription disabled")
        return ""
    
    try:
        with open(audio_path, "rb") as audio_file:
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": audio_file},
                data={"model": "whisper-1", "language": "en"}
            )
        
        if response.status_code == 200:
            transcript = response.json().get("text", "")
            print(f"🎤 Whisper transcript: {transcript}")
            return transcript
        else:
            print(f"❌ Whisper API error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"❌ Audio transcription failed: {e}")
        return ""

def transcribe_audio_local(audio_path: str) -> str:
    """
    Alternative: Use local Whisper model (requires: pip install openai-whisper)
    """
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        transcript = result["text"]
        print(f"🎤 Local Whisper: {transcript}")
        return transcript
    except ImportError:
        print("⚠️ Local whisper not installed. Install: pip install openai-whisper")
        return ""
    except Exception as e:
        print(f"❌ Local transcription failed: {e}")
        return ""

# ============================
# SEARCH HELPERS
# ============================
def cosine_to_percent(score):
    """Convert FAISS IndexFlatIP score to percentage"""
    return float((score + 1.0) / 2.0)

def search_with_embedding(embedding, index, k=20, color_filter=None):
    """Search with embedding and apply color filter with scoring boost"""
    if index is None or id_map is None:
        return []
    
    # Search more results initially to account for color filtering
    search_k = k * 10 if color_filter else k * 5
    distances, indices = index.search(embedding, search_k)
    results = []
    
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
            
        product_id = int(id_map[int(idx)])
        p = products.get(product_id)
        if not p:
            continue
        
        score = cosine_to_percent(dist)
        
        # Apply color filter
        if color_filter:
            if not product_matches_color(p, color_filter):
                continue
            
            # BOOST score for color matches
            # Give significant advantage to items with matching color
            score = min(1.0, score * 1.25)  # 25% boost for color match
        
        results.append({
            "id": product_id,
            "name": p.get("productDisplayName"),
            "category": p.get("masterCategory", ""),
            "subCategory": p.get("subCategory", ""),
            "image": p.get("image_path"),
            "color": p.get("color", "unknown"),
            "has_3d_model": p.get("has_3d_model", False),
            "score": float(score),
        })
        
        # Stop if we have enough results
        if len(results) >= k * 2:
            break
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

# ============================
# MAIN SEARCH ENDPOINT
# ============================
@app.post("/search/intelligent")
async def intelligent_search(
    query: str = Form(""),
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    top_k: int = Form(10),
    session_id: str = Form("default"),
):
    """
    Multimodal Search supporting:
    - Text query
    - Image upload (visual search)
    - Audio upload (voice search)
    """
    try:
        print(f"\n🔍 Search: query='{query}', image={image is not None}, audio={audio is not None}")
        
        modality_embeddings = []
        modality_info = {"text": False, "image": False, "audio": False}
        
        # ========== PROCESS AUDIO ==========
        audio_transcript = ""
        if audio:
            print("🎤 Processing audio...")
            try:
                # Save audio temporarily
                audio_suffix = ".wav" if "wav" in (audio.filename or "") else ".mp3"
                tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix)
                tmp_audio.write(await audio.read())
                tmp_audio.close()
                
                # Transcribe audio to text
                if OPENAI_API_KEY:
                    audio_transcript = transcribe_audio_whisper(tmp_audio.name)
                else:
                    audio_transcript = transcribe_audio_local(tmp_audio.name)
                
                # Clean up
                os.remove(tmp_audio.name)
                
                if audio_transcript:
                    modality_info["audio"] = True
                    # Merge audio transcript with query
                    if query.strip():
                        query = f"{query} {audio_transcript}"
                    else:
                        query = audio_transcript
                    print(f"✅ Audio transcribed: '{audio_transcript}'")
                
            except Exception as e:
                print(f"⚠️ Audio processing error: {e}")
        
        # ========== PROCESS IMAGE ==========
        image_desc = None
        uploaded_img_path = None
        
        if image:
            print("🖼️ Processing image...")
            try:
                tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp_img.write(await image.read())
                tmp_img.close()
                uploaded_img_path = tmp_img.name
                
                # Get image description with Gemini
                if GEMINI_API_KEY:
                    image_desc = analyze_image_gemini(uploaded_img_path)
                    print(f"🖼️ Gemini: {image_desc}")
                
                # Detect color from uploaded image
                detected_image_color = detect_color_from_image(uploaded_img_path)
                if detected_image_color and not color_filter:
                    # Use image color if no text color specified
                    color_filter = detected_image_color
                    print(f"🎨 Using color from uploaded image: {color_filter}")
                
                # Get image embedding with CLIP
                clip_model, clip_processor = get_clip()
                with torch.no_grad():
                    pil_img = Image.open(uploaded_img_path).convert("RGB")
                    img_inputs = clip_processor(images=pil_img, return_tensors="pt").to(device)
                    img_emb = clip_model.get_image_features(pixel_values=img_inputs['pixel_values'])
                    img_emb = img_emb.cpu().numpy()
                    img_emb /= np.linalg.norm(img_emb, axis=1, keepdims=True)
                
                modality_embeddings.append(img_emb[0])
                modality_info["image"] = True
                
                # Clean up
                os.remove(uploaded_img_path)
                
            except Exception as e:
                print(f"⚠️ Image processing error: {e}")
                if uploaded_img_path and os.path.exists(uploaded_img_path):
                    os.remove(uploaded_img_path)
        
        # ========== PROCESS TEXT ==========
        if query.strip():
            print(f"📝 Processing text: '{query}'")
            
            # Extract color filter BEFORE embedding
            color_filter = extract_color_from_query(query)
            print(f"🎨 Detected color: {color_filter}")
            
            # If color is specified, emphasize it in the query for CLIP
            if color_filter:
                # Duplicate color keyword for stronger signal
                query_with_emphasis = f"{color_filter} {color_filter} {query}"
            else:
                query_with_emphasis = query
            
            # Get text embedding with CLIP
            clip_model, clip_processor = get_clip()
            
            # Clean query (max 50 words to avoid token limit)
            words = query_with_emphasis.split()
            clean_query = " ".join(words[:50])
            
            with torch.no_grad():
                txt_inputs = clip_processor(
                    text=[clean_query],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=77
                ).to(device)
                txt_emb = clip_model.get_text_features(**txt_inputs)
                txt_emb = txt_emb.cpu().numpy()
                txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)
            
            modality_embeddings.append(txt_emb[0])
            modality_info["text"] = True
        else:
            color_filter = None
        
        # ========== COMBINE EMBEDDINGS ==========
        if not modality_embeddings:
            return JSONResponse(
                status_code=400,
                content={"error": "No input provided (text, image, or audio required)"}
            )
        
        # Average embeddings from different modalities
        final_embedding = np.mean(modality_embeddings, axis=0, keepdims=True)
        final_embedding /= np.linalg.norm(final_embedding, axis=1, keepdims=True)
        final_embedding = final_embedding.astype("float32")
        
        print(f"🔗 Combined {len(modality_embeddings)} modalities")
        
        # ========== SEARCH ==========
        # Use image index if image was primary input, else text index
        search_index = image_index if modality_info["image"] and not modality_info["text"] else text_index
        
        all_results = search_with_embedding(
            final_embedding, 
            search_index, 
            k=top_k * 3, 
            color_filter=color_filter
        )
        
        # Split by score - STRICTER thresholds when color is specified
        if color_filter:
            # When color is specified, be more demanding about matches
            accurate = [r for r in all_results if r["score"] >= 0.75]
            related = [r for r in all_results if 0.60 <= r["score"] < 0.75]
        else:
            # Normal thresholds for non-color queries
            accurate = [r for r in all_results if r["score"] >= 0.72]
            related = [r for r in all_results if 0.55 <= r["score"] < 0.72]
        
        if not accurate and related:
            accurate = related[:5]
            related = related[5:]
        
        # ========== GENERATE SUMMARY ==========
        ai_summary = ""
        if GROQ_API_KEY and accurate:
            top_names = ", ".join([r["name"] for r in accurate[:3]])
            
            modalities_used = []
            if modality_info["text"]: modalities_used.append("text")
            if modality_info["image"]: modalities_used.append("image")
            if modality_info["audio"]: modalities_used.append("voice")
            
            messages = [
                {"role": "system", "content": "You are a helpful furniture shopping assistant."},
                {"role": "user", "content": f"""User searched using: {', '.join(modalities_used)}
Query: "{query}"
{f"Audio said: '{audio_transcript}'" if audio_transcript else ""}
{f"Image shows: {image_desc}" if image_desc else ""}
Found {len(accurate)} matches: {top_names}

Write 2-3 friendly sentences about the results."""}
            ]
            ai_summary = call_groq(messages, temperature=0.7)
        
        if not ai_summary:
            ai_summary = f"Found {len(accurate)} items matching your search."
        
        print(f"✅ Results: {len(accurate)} accurate, {len(related)} related")
        
        return {
            "query": query,
            "audio_transcript": audio_transcript,
            "image_description": image_desc,
            "interpreted_query": query[:100],
            "ai_summary": ai_summary,
            "accurate_results": accurate[:top_k],
            "related_results": related[:top_k],
            "total_found": len(all_results),
            "color_detected": color_filter,
            "modalities_used": modality_info,
            "llm_status": {
                "vision": "gemini" if image_desc else "none",
                "reasoning": "groq" if GROQ_API_KEY else "none",
                "audio": "whisper" if audio_transcript else "none",
            }
        }
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": "Search failed", "details": str(e)}
        )

# ============================
# AR ENDPOINT
# ============================
@app.get("/products/{product_id}/ar-info")
def get_ar_info(product_id: int):
    product = products.get(product_id)
    if not product:
        return JSONResponse(
            status_code=404,
            content={"error": "Product not found", "ar_available": False}
        )
    
    glb_path = Path(f"{MODELS_DIR}/{product_id}.glb")
    base_url = "http://localhost:8000"
    
    ar_available = glb_path.exists()
    model_size_kb = 0
    
    if ar_available:
        model_size_kb = glb_path.stat().st_size // 1024
    
    return {
        "product_id": product_id,
        "name": product.get("productDisplayName"),
        "category": product.get("masterCategory", ""),
        "color": product.get("color", "unknown"),
        "model_url": f"{base_url}/models/{product_id}.glb" if ar_available else None,
        "poster_url": f"{base_url}/static/{product.get('image_path')}",
        "model_size_kb": model_size_kb,
        "ar_available": ar_available,
        "has_3d_model": ar_available,
    }

# ============================
# MISC ROUTES
# ============================
@app.get("/")
def root():
    return {
        "message": "Multimodal Search API with AR & Voice",
        "products": len(products),
        "categories": CATEGORIES,
        "features": {
            "text_search": True,
            "image_search": bool(image_index),
            "voice_search": bool(OPENAI_API_KEY),
            "ar_viewer": True,
            "ai_vision": bool(GEMINI_API_KEY),
            "ai_reasoning": bool(GROQ_API_KEY),
        }
    }

@app.post("/conversation/reset")
async def reset_conversation(session_id: str = Form("default")):
    return {"message": f"Session {session_id} reset"}

# ============================
# CORS
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MULTIMODAL SEARCH SERVER")
    print("=" * 60)
    print(f"📦 Products: {len(products)}")
    print(f"🖼️  Gemini (vision): {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"🧠 Groq (reasoning): {'✅' if GROQ_API_KEY else '❌'}")
    print(f"🎤 Whisper (audio): {'✅' if OPENAI_API_KEY else '⚠️ local only'}")
    print(f"📱 AR Models: {sum(1 for p in products.values() if p.get('has_3d_model'))}")
    print("=" * 60)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)






# import os
# import json
# import tempfile
# from pathlib import Path
# from typing import Optional, List, Dict

# import uvicorn
# import faiss
# import numpy as np
# import torch
# import requests
# from fastapi import FastAPI, UploadFile, File, Form
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from transformers import CLIPProcessor, CLIPModel
# from PIL import Image
# from dotenv import load_dotenv

# # ============================
# # ENV + CONFIG
# # ============================
# load_dotenv(".env.local")
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# DATA_IMAGES_DIR = "data/images"
# CLEAN_PRODUCTS_PATH = "data/clean_products.json"
# IMAGE_INDEX_PATH = "data/image_index.faiss"
# TEXT_INDEX_PATH = "data/text_index.faiss"
# ID_MAP_PATH = "data/id_map.npy"
# MODELS_DIR = "data/models"

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # For Whisper (audio transcription)

# # Gemini setup
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
#     if GEMINI_API_KEY:
#         genai.configure(api_key=GEMINI_API_KEY)
#         print("✅ Gemini configured")
#     else:
#         print("⚠️ Gemini key missing")
# except ImportError:
#     GEMINI_AVAILABLE = False
#     print("⚠️ Gemini library not installed")

# # ============================
# # FASTAPI + MODELS
# # ============================
# app = FastAPI(title="Multimodal Search with AR & Voice")
# app.mount("/static", StaticFiles(directory=DATA_IMAGES_DIR), name="static")
# app.mount("/models", StaticFiles(directory=MODELS_DIR), name="models")

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# torch.set_grad_enabled(False)

# # ============================
# # SAFE LOADERS
# # ============================
# def safe_load_faiss(path):
#     if os.path.exists(path):
#         return faiss.read_index(path)
#     print(f"⚠️ FAISS not found: {path}")
#     return None

# def safe_load_npy(path):
#     if os.path.exists(path):
#         return np.load(path)
#     print(f"⚠️ NPY not found: {path}")
#     return None

# def safe_load_json(path):
#     if os.path.exists(path):
#         with open(path, "r", encoding="utf-8") as f:
#             return {int(p["id"]): p for p in json.load(f)}
#     print(f"⚠️ JSON not found: {path}")
#     return {}

# print("📦 Loading FAISS indexes and metadata...")
# image_index = safe_load_faiss(IMAGE_INDEX_PATH)
# text_index = safe_load_faiss(TEXT_INDEX_PATH)
# id_map = safe_load_npy(ID_MAP_PATH)
# products = safe_load_json(CLEAN_PRODUCTS_PATH)

# CATEGORIES = list(set(p.get("subCategory", "") for p in products.values() if p.get("subCategory")))
# print(f"✅ Loaded {len(products)} products")

# # ============================
# # CLIP MODEL
# # ============================
# clip_model = None
# clip_processor = None

# def get_clip():
#     global clip_model, clip_processor
#     if clip_model is None:
#         print("🔠 Loading CLIP model...")
#         clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
#         clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
#         clip_model.eval()
#     return clip_model, clip_processor

# # ============================
# # COLOR DETECTION
# # ============================
# COMMON_COLORS = [
#     "red", "blue", "green", "yellow", "black", "white", "brown", "grey", "gray",
#     "pink", "purple", "orange", "beige", "navy", "burgundy", "maroon", "tan"
# ]

# def extract_color_from_query(query: str) -> Optional[str]:
#     query_lower = query.lower()
#     for color in COMMON_COLORS:
#         if color in query_lower:
#             return color
#     return None

# def product_matches_color(product: Dict, color: str) -> bool:
#     if not color:
#         return True
#     name = product.get("productDisplayName", "").lower()
#     prod_color = product.get("color", "").lower()
#     return color in name or color in prod_color

# # ============================
# # LLM HELPERS
# # ============================
# def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
#     if not GROQ_API_KEY:
#         return ""
#     try:
#         res = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
#             json={
#                 "model": "llama-3.3-70b-versatile",
#                 "messages": messages,
#                 "temperature": temperature,
#                 "max_tokens": 400,
#             },
#             timeout=20,
#         )
#         if res.status_code == 200:
#             return res.json()["choices"][0]["message"]["content"]
#     except Exception as e:
#         print(f"❌ Groq error: {e}")
#     return ""

# def analyze_image_gemini(image_path: str) -> str:
#     if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
#         return ""
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         img = Image.open(image_path)
#         prompt = "Describe this furniture in 5-10 words: type, color, material."
#         response = model.generate_content([prompt, img])
#         return response.text.strip()[:100]
#     except Exception as e:
#         print(f"⚠️ Gemini error: {e}")
#     return ""

# # ============================
# # AUDIO TRANSCRIPTION (WHISPER)
# # ============================
# def transcribe_audio_whisper(audio_path: str) -> str:
#     """
#     Transcribe audio to text using OpenAI Whisper API
#     """
#     if not OPENAI_API_KEY:
#         print("⚠️ OpenAI API key not set - audio transcription disabled")
#         return ""
    
#     try:
#         with open(audio_path, "rb") as audio_file:
#             response = requests.post(
#                 "https://api.openai.com/v1/audio/transcriptions",
#                 headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
#                 files={"file": audio_file},
#                 data={"model": "whisper-1", "language": "en"}
#             )
        
#         if response.status_code == 200:
#             transcript = response.json().get("text", "")
#             print(f"🎤 Whisper transcript: {transcript}")
#             return transcript
#         else:
#             print(f"❌ Whisper API error: {response.status_code}")
#             return ""
#     except Exception as e:
#         print(f"❌ Audio transcription failed: {e}")
#         return ""

# def transcribe_audio_local(audio_path: str) -> str:
#     """
#     Alternative: Use local Whisper model (requires: pip install openai-whisper)
#     """
#     try:
#         import whisper
#         model = whisper.load_model("base")
#         result = model.transcribe(audio_path)
#         transcript = result["text"]
#         print(f"🎤 Local Whisper: {transcript}")
#         return transcript
#     except ImportError:
#         print("⚠️ Local whisper not installed. Install: pip install openai-whisper")
#         return ""
#     except Exception as e:
#         print(f"❌ Local transcription failed: {e}")
#         return ""

# # ============================
# # SEARCH HELPERS
# # ============================
# def cosine_to_percent(score):
#     """Convert FAISS IndexFlatIP score to percentage"""
#     return float((score + 1.0) / 2.0)

# def search_with_embedding(embedding, index, k=20, color_filter=None):
#     if index is None or id_map is None:
#         return []
    
#     distances, indices = index.search(embedding, k * 5)
#     results = []
    
#     for dist, idx in zip(distances[0], indices[0]):
#         if idx < 0 or len(results) >= k * 2:
#             continue
            
#         product_id = int(id_map[int(idx)])
#         p = products.get(product_id)
#         if not p:
#             continue
        
#         # Color filter
#         if color_filter and not product_matches_color(p, color_filter):
#             continue
        
#         score = cosine_to_percent(dist)
#         results.append({
#             "id": product_id,
#             "name": p.get("productDisplayName"),
#             "category": p.get("masterCategory", ""),
#             "subCategory": p.get("subCategory", ""),
#             "image": p.get("image_path"),
#             "color": p.get("color", "unknown"),
#             "has_3d_model": p.get("has_3d_model", False),
#             "score": float(score),
#         })
    
#     return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

# # ============================
# # MAIN SEARCH ENDPOINT
# # ============================
# @app.post("/search/intelligent")
# async def intelligent_search(
#     query: str = Form(""),
#     image: UploadFile = File(None),
#     audio: UploadFile = File(None),
#     top_k: int = Form(10),
#     session_id: str = Form("default"),
# ):
#     """
#     Multimodal Search supporting:
#     - Text query
#     - Image upload (visual search)
#     - Audio upload (voice search)
#     """
#     try:
#         print(f"\n🔍 Search: query='{query}', image={image is not None}, audio={audio is not None}")
        
#         modality_embeddings = []
#         modality_info = {"text": False, "image": False, "audio": False}
        
#         # ========== PROCESS AUDIO ==========
#         audio_transcript = ""
#         if audio:
#             print("🎤 Processing audio...")
#             try:
#                 # Save audio temporarily
#                 audio_suffix = ".wav" if "wav" in (audio.filename or "") else ".mp3"
#                 tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix)
#                 tmp_audio.write(await audio.read())
#                 tmp_audio.close()
                
#                 # Transcribe audio to text
#                 if OPENAI_API_KEY:
#                     audio_transcript = transcribe_audio_whisper(tmp_audio.name)
#                 else:
#                     audio_transcript = transcribe_audio_local(tmp_audio.name)
                
#                 # Clean up
#                 os.remove(tmp_audio.name)
                
#                 if audio_transcript:
#                     modality_info["audio"] = True
#                     # Merge audio transcript with query
#                     if query.strip():
#                         query = f"{query} {audio_transcript}"
#                     else:
#                         query = audio_transcript
#                     print(f"✅ Audio transcribed: '{audio_transcript}'")
                
#             except Exception as e:
#                 print(f"⚠️ Audio processing error: {e}")
        
#         # ========== PROCESS IMAGE ==========
#         image_desc = None
#         uploaded_img_path = None
        
#         if image:
#             print("🖼️ Processing image...")
#             try:
#                 tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
#                 tmp_img.write(await image.read())
#                 tmp_img.close()
#                 uploaded_img_path = tmp_img.name
                
#                 # Get image description with Gemini
#                 if GEMINI_API_KEY:
#                     image_desc = analyze_image_gemini(uploaded_img_path)
#                     print(f"🖼️ Gemini: {image_desc}")
                
#                 # Get image embedding with CLIP
#                 clip_model, clip_processor = get_clip()
#                 with torch.no_grad():
#                     pil_img = Image.open(uploaded_img_path).convert("RGB")
#                     img_inputs = clip_processor(images=pil_img, return_tensors="pt").to(device)
#                     img_emb = clip_model.get_image_features(pixel_values=img_inputs['pixel_values'])
#                     img_emb = img_emb.cpu().numpy()
#                     img_emb /= np.linalg.norm(img_emb, axis=1, keepdims=True)
                
#                 modality_embeddings.append(img_emb[0])
#                 modality_info["image"] = True
                
#                 # Clean up
#                 os.remove(uploaded_img_path)
                
#             except Exception as e:
#                 print(f"⚠️ Image processing error: {e}")
#                 if uploaded_img_path and os.path.exists(uploaded_img_path):
#                     os.remove(uploaded_img_path)
        
#         # ========== PROCESS TEXT ==========
#         if query.strip():
#             print(f"📝 Processing text: '{query}'")
            
#             # Extract color filter
#             color_filter = extract_color_from_query(query)
            
#             # Get text embedding with CLIP
#             clip_model, clip_processor = get_clip()
            
#             # Clean query (max 50 words to avoid token limit)
#             words = query.split()
#             clean_query = " ".join(words[:50])
            
#             with torch.no_grad():
#                 txt_inputs = clip_processor(
#                     text=[clean_query],
#                     return_tensors="pt",
#                     padding=True,
#                     truncation=True,
#                     max_length=77
#                 ).to(device)
#                 txt_emb = clip_model.get_text_features(**txt_inputs)
#                 txt_emb = txt_emb.cpu().numpy()
#                 txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)
            
#             modality_embeddings.append(txt_emb[0])
#             modality_info["text"] = True
#         else:
#             color_filter = None
        
#         # ========== COMBINE EMBEDDINGS ==========
#         if not modality_embeddings:
#             return JSONResponse(
#                 status_code=400,
#                 content={"error": "No input provided (text, image, or audio required)"}
#             )
        
#         # Average embeddings from different modalities
#         final_embedding = np.mean(modality_embeddings, axis=0, keepdims=True)
#         final_embedding /= np.linalg.norm(final_embedding, axis=1, keepdims=True)
#         final_embedding = final_embedding.astype("float32")
        
#         print(f"🔗 Combined {len(modality_embeddings)} modalities")
        
#         # ========== SEARCH ==========
#         # Use image index if image was primary input, else text index
#         search_index = image_index if modality_info["image"] and not modality_info["text"] else text_index
        
#         all_results = search_with_embedding(
#             final_embedding, 
#             search_index, 
#             k=top_k * 3, 
#             color_filter=color_filter
#         )
        
#         # Split by score
#         accurate = [r for r in all_results if r["score"] >= 0.72]
#         related = [r for r in all_results if 0.55 <= r["score"] < 0.72]
        
#         if not accurate and related:
#             accurate = related[:5]
#             related = related[5:]
        
#         # ========== GENERATE SUMMARY ==========
#         ai_summary = ""
#         if GROQ_API_KEY and accurate:
#             top_names = ", ".join([r["name"] for r in accurate[:3]])
            
#             modalities_used = []
#             if modality_info["text"]: modalities_used.append("text")
#             if modality_info["image"]: modalities_used.append("image")
#             if modality_info["audio"]: modalities_used.append("voice")
            
#             messages = [
#                 {"role": "system", "content": "You are a helpful furniture shopping assistant."},
#                 {"role": "user", "content": f"""User searched using: {', '.join(modalities_used)}
# Query: "{query}"
# {f"Audio said: '{audio_transcript}'" if audio_transcript else ""}
# {f"Image shows: {image_desc}" if image_desc else ""}
# Found {len(accurate)} matches: {top_names}

# Write 2-3 friendly sentences about the results."""}
#             ]
#             ai_summary = call_groq(messages, temperature=0.7)
        
#         if not ai_summary:
#             ai_summary = f"Found {len(accurate)} items matching your search."
        
#         print(f"✅ Results: {len(accurate)} accurate, {len(related)} related")
        
#         return {
#             "query": query,
#             "audio_transcript": audio_transcript,
#             "image_description": image_desc,
#             "interpreted_query": query[:100],
#             "ai_summary": ai_summary,
#             "accurate_results": accurate[:top_k],
#             "related_results": related[:top_k],
#             "total_found": len(all_results),
#             "color_detected": color_filter,
#             "modalities_used": modality_info,
#             "llm_status": {
#                 "vision": "gemini" if image_desc else "none",
#                 "reasoning": "groq" if GROQ_API_KEY else "none",
#                 "audio": "whisper" if audio_transcript else "none",
#             }
#         }
        
#     except Exception as e:
#         print(f"❌ Search error: {e}")
#         import traceback
#         traceback.print_exc()
#         return JSONResponse(
#             status_code=500,
#             content={"error": "Search failed", "details": str(e)}
#         )

# # ============================
# # AR ENDPOINT
# # ============================
# @app.get("/products/{product_id}/ar-info")
# def get_ar_info(product_id: int):
#     product = products.get(product_id)
#     if not product:
#         return JSONResponse(
#             status_code=404,
#             content={"error": "Product not found", "ar_available": False}
#         )
    
#     glb_path = Path(f"{MODELS_DIR}/{product_id}.glb")
#     base_url = "http://localhost:8000"
    
#     ar_available = glb_path.exists()
#     model_size_kb = 0
    
#     if ar_available:
#         model_size_kb = glb_path.stat().st_size // 1024
    
#     return {
#         "product_id": product_id,
#         "name": product.get("productDisplayName"),
#         "category": product.get("masterCategory", ""),
#         "color": product.get("color", "unknown"),
#         "model_url": f"{base_url}/models/{product_id}.glb" if ar_available else None,
#         "poster_url": f"{base_url}/static/{product.get('image_path')}",
#         "model_size_kb": model_size_kb,
#         "ar_available": ar_available,
#         "has_3d_model": ar_available,
#     }

# # ============================
# # MISC ROUTES
# # ============================
# @app.get("/")
# def root():
#     return {
#         "message": "Multimodal Search API with AR & Voice",
#         "products": len(products),
#         "categories": CATEGORIES,
#         "features": {
#             "text_search": True,
#             "image_search": bool(image_index),
#             "voice_search": bool(OPENAI_API_KEY),
#             "ar_viewer": True,
#             "ai_vision": bool(GEMINI_API_KEY),
#             "ai_reasoning": bool(GROQ_API_KEY),
#         }
#     }

# @app.post("/conversation/reset")
# async def reset_conversation(session_id: str = Form("default")):
#     return {"message": f"Session {session_id} reset"}

# # ============================
# # CORS
# # ============================
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# if __name__ == "__main__":
#     print("=" * 60)
#     print("🚀 MULTIMODAL SEARCH SERVER")
#     print("=" * 60)
#     print(f"📦 Products: {len(products)}")
#     print(f"🖼️  Gemini (vision): {'✅' if GEMINI_API_KEY else '❌'}")
#     print(f"🧠 Groq (reasoning): {'✅' if GROQ_API_KEY else '❌'}")
#     print(f"🎤 Whisper (audio): {'✅' if OPENAI_API_KEY else '⚠️ local only'}")
#     print(f"📱 AR Models: {sum(1 for p in products.values() if p.get('has_3d_model'))}")
#     print("=" * 60)
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)