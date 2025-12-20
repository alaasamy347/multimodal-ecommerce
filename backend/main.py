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
# # KAGGLE
# # ============================
# IS_KAGGLE = os.path.exists("/kaggle/input")

# if IS_KAGGLE:
#     KAGGLE_DATASET = "/kaggle/input/amazon-data2"
#     BASE_DATA_DIR = KAGGLE_DATASET
#     OUTPUT_DIR = "/kaggle/working"
# else:
#     BASE_DATA_DIR = "data"
#     OUTPUT_DIR = "data"

# # ============================
# # ENV + CONFIG
# # ============================
# load_dotenv(".env.local")
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# # DATA_IMAGES_DIR = "data/images"
# # CLEAN_PRODUCTS_PATH = "data/clean_products.json"
# # IMAGE_INDEX_PATH = "data/image_index.faiss"
# # TEXT_INDEX_PATH = "data/text_index.faiss"
# # ID_MAP_PATH = "data/id_map.npy"
# # MODELS_DIR = "data/models"

# DATA_IMAGES_DIR = os.path.join(BASE_DATA_DIR, "images")
# CLEAN_PRODUCTS_PATH = os.path.join(BASE_DATA_DIR, "clean_products.json")
# IMAGE_INDEX_PATH = os.path.join(BASE_DATA_DIR, "image_index.faiss")
# TEXT_INDEX_PATH = os.path.join(BASE_DATA_DIR, "text_index.faiss")
# ID_MAP_PATH = os.path.join(BASE_DATA_DIR, "id_map.npy")
# MODELS_DIR = os.path.join(BASE_DATA_DIR, "models")

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
# # CLIP MODEL (SYNCHRONOUS LOAD)
# # ============================
# clip_model = None
# clip_processor = None

# # This function is now just a getter, the model loads immediately below
# def get_clip():
#     global clip_model, clip_processor
#     # We assume model is loaded below, but keep this check for safety
#     if clip_model is None:
#         print("🔠 Loading CLIP model...")
#         clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
#         clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
#         clip_model.eval()
#     return clip_model, clip_processor

# # Load CLIP model on startup outside of a function
# print("🔠 Loading CLIP model...")
# clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
# clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
# clip_model.eval()

# # ============================
# # IMAGE COLOR DETECTION
# # ============================
# COMMON_COLORS = [
#     "red", "blue", "green", "yellow", "black", "white", "brown", "grey", "gray",
#     "pink", "purple", "orange", "beige", "navy", "burgundy", "maroon", "tan"
# ]

# def detect_color_from_image(image_path: str) -> Optional[str]:
#     """Detect dominant color from uploaded image"""
#     try:
#         from PIL import Image
#         import numpy as np
        
#         img = Image.open(image_path).convert('RGB')
#         img = img.resize((100, 100))
        
#         pixels = np.array(img).reshape(-1, 3)
#         avg_color = np.mean(pixels, axis=0)
        
#         def rgb_to_color_name(rgb):
#             r, g, b = rgb
#             if max(r, g, b) < 80: return "black"
#             if min(r, g, b) > 200: return "white"
            
#             if r > g + 30 and r > b + 30:
#                 if r > 180 and g < 100: return "red"
#                 elif r > 150 and g > 100: return "orange"
#                 else: return "pink"
#             elif g > r + 30 and g > b + 30: return "green"
#             elif b > r + 30 and b > g + 30: return "blue"
#             elif r > 150 and g > 120 and b < 100: return "orange"
#             elif r > 120 and g > 100 and b > 120: return "purple"
#             elif abs(r - g) < 30 and abs(g - b) < 30:
#                 if r > 150: return "white"
#                 elif r > 100: return "grey"
#                 else: return "black"
#             elif r > 100 and g > 80 and b < 80: return "brown"
#             return None
        
#         color_name = rgb_to_color_name(avg_color)
#         print(f"🎨 Image color detected: {color_name}")
#         return color_name
        
#     except Exception as e:
#         print(f"⚠️ Color detection failed: {e}")
#         return None

# def extract_color_from_query(query: str) -> Optional[str]:
#     query_lower = query.lower()
#     for color in COMMON_COLORS:
#         if color in query_lower:
#             return color
#     return None

# def product_matches_color(product: Dict, color: str) -> bool:
#     if not color: return True
#     name = product.get("productDisplayName", "").lower()
#     prod_color = product.get("color", "").lower()
#     color_groups = {
#         "red": ["red", "crimson", "burgundy", "maroon", "scarlet", "ruby"],
#         "blue": ["blue", "navy", "azure", "cobalt", "indigo", "sapphire"],
#         "green": ["green", "olive", "emerald", "lime", "forest", "mint"],
#         "yellow": ["yellow", "gold", "golden", "amber", "cream"],
#         "black": ["black", "ebony", "charcoal", "dark"],
#         "white": ["white", "ivory", "cream", "off-white", "beige"],
#         "brown": ["brown", "tan", "beige", "chocolate", "mocha", "walnut", "oak"],
#         "grey": ["grey", "gray", "silver", "slate"],
#         "pink": ["pink", "rose", "blush", "magenta", "coral"],
#         "purple": ["purple", "violet", "lavender", "plum", "mauve"],
#         "orange": ["orange", "coral", "peach", "tangerine"],
#     }
    
#     color_variations = color_groups.get(color, [color])
#     for variation in color_variations:
#         if variation in name or variation in prod_color: return True
#     return False

# # ============================
# # LLM HELPERS
# # ============================
# def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
#     if not GROQ_API_KEY: return ""
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
#         if res.status_code == 200: return res.json()["choices"][0]["message"]["content"]
#     except Exception as e:
#         print(f"❌ Groq error: {e}")
#     return ""

# def analyze_image_gemini(image_path: str) -> str:
#     if not GEMINI_AVAILABLE or not GEMINI_API_KEY: return ""
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
#     """Transcribe audio to text using OpenAI Whisper API"""
#     if not OPENAI_API_KEY:
#         print("⚠️ OpenAI API key not set - audio transcription disabled")
#         return ""
    
#     try:
#         # Note: Whisper requires the audio file to be opened in binary mode for the API call
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

# # Fallback for local testing if local whisper is installed
# def transcribe_audio_local(audio_path: str) -> str:
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
#     return float((score + 1.0) / 2.0)

# def search_with_embedding(embedding, index, k=20, color_filter=None):
#     if index is None or id_map is None: return []
    
#     search_k = k * 10 if color_filter else k * 5
#     distances, indices = index.search(embedding, search_k)
#     results = []
    
#     for dist, idx in zip(distances[0], indices[0]):
#         if idx < 0: continue
            
#         product_id = int(id_map[int(idx)])
#         p = products.get(product_id)
#         if not p: continue
        
#         score = cosine_to_percent(dist)
        
#         if color_filter:
#             if not product_matches_color(p, color_filter): continue
#             score = min(1.0, score * 1.25) # 25% boost for color match
        
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
        
#         if len(results) >= k * 2: break
    
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
#         color_filter = None
#         clean_query = query
        
#         # ========== PROCESS AUDIO ==========
#         if audio:
#             # ... (Audio processing logic remains the same)
#             print("🎤 Processing audio...")
#             try:
#                 audio_suffix = ".wav" if "wav" in (audio.filename or "") else ".mp3"
#                 tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=audio_suffix)
#                 tmp_audio.write(await audio.read())
#                 tmp_audio.close()
                
#                 audio_transcript = transcribe_audio_whisper(tmp_audio.name) if OPENAI_API_KEY else transcribe_audio_local(tmp_audio.name)
                
#                 os.remove(tmp_audio.name)
                
#                 if audio_transcript:
#                     modality_info["audio"] = True
#                     query = f"{query} {audio_transcript}".strip()
#                     print(f"✅ Audio transcribed, new query: '{query}'")
#             except Exception as e:
#                 print(f"⚠️ Audio processing error: {e}")
        
#         # ========== PROCESS IMAGE ==========
#         image_desc = None
#         uploaded_img_path = None
        
#         if image:
#             # ... (Image processing logic remains the same)
#             print("🖼️ Processing image...")
#             try:
#                 tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
#                 tmp_img.write(await image.read())
#                 tmp_img.close()
#                 uploaded_img_path = tmp_img.name
                
#                 if GEMINI_API_KEY:
#                     image_desc = analyze_image_gemini(uploaded_img_path)
                
#                 detected_image_color = detect_color_from_image(uploaded_img_path)
#                 if detected_image_color:
#                     color_filter = detected_image_color
#                     print(f"🎨 Using color from uploaded image: {color_filter}")
                
#                 # Get image embedding (CLIP is loaded globally)
#                 with torch.no_grad():
#                     pil_img = Image.open(uploaded_img_path).convert("RGB")
#                     img_inputs = clip_processor(images=pil_img, return_tensors="pt").to(device)
#                     img_emb = clip_model.get_image_features(pixel_values=img_inputs['pixel_values'])
#                     img_emb = img_emb.cpu().numpy()
#                     img_emb /= np.linalg.norm(img_emb, axis=1, keepdims=True)
                
#                 modality_embeddings.append(img_emb[0])
#                 modality_info["image"] = True
#                 os.remove(uploaded_img_path)
#             except Exception as e:
#                 print(f"⚠️ Image processing error: {e}")
#                 if uploaded_img_path and os.path.exists(uploaded_img_path): os.remove(uploaded_img_path)
        
#         # ========== PROCESS TEXT ==========
#         if query.strip():
#             print(f"📝 Processing text: '{query}'")
            
#             # Use text color filter if it exists, otherwise rely on image color (if any)
#             text_color = extract_color_from_query(query)
#             if text_color:
#                 color_filter = text_color
#             print(f"🎨 Final color filter: {color_filter}")
            
#             query_with_emphasis = f"{color_filter} {color_filter} {query}" if color_filter else query
            
#             words = query_with_emphasis.split()
#             clean_query = " ".join(words[:50])
            
#             # Get text embedding (CLIP is loaded globally)
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
        
#         # ========== COMBINE EMBEDDINGS ==========
#         if not modality_embeddings:
#             return JSONResponse(
#                 status_code=400,
#                 content={"error": "No input provided (text, image, or audio required)"}
#             )
        
#         final_embedding = np.mean(modality_embeddings, axis=0, keepdims=True)
#         final_embedding /= np.linalg.norm(final_embedding, axis=1, keepdims=True)
#         final_embedding = final_embedding.astype("float32")
        
#         print(f"🔗 Combined {len(modality_embeddings)} modalities")
        
#         # ========== SEARCH ==========
#         search_index = image_index if modality_info["image"] and not modality_info["text"] else text_index
        
#         all_results = search_with_embedding(
#             final_embedding, 
#             search_index, 
#             k=top_k * 3, 
#             color_filter=color_filter
#         )
        
#         # Split results
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
#                 {"role": "user", "content": f"""User searched using: {', '.join(modalities_used)} and the query: "{query}". I found {len(accurate)} great matches like {top_names}. Write a short (2-3 sentence) conversational summary describing the results and acknowledging the input type(s)."""},
#             ]
#             ai_summary = call_groq(messages, temperature=0.7)
        
#         # ========== FINAL RETURN ==========
#         return {
#             "query": query,
#             "interpreted_query": clean_query,
#             "ai_summary": ai_summary,
#             "accurate_results": accurate[:top_k],
#             "related_results": related[:top_k],
#             "color_filter": color_filter,
#             "llm_status": {
#                 "vision": "gemini" if image_desc else "none",
#                 "reasoning": "groq" if GROQ_API_KEY else "none",
#                 "audio": "whisper" if modality_info["audio"] else "none",
#             },
#         }
        
#     except Exception as e:
#         print(f"❌ Critical Search Error: {e}")
#         return JSONResponse(
#             status_code=500,
#             content={"error": f"An internal server error occurred: {e}"}
#         )

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
#     # IMPORTANT: Use the actual deployed Vercel URL instead of localhost/127.0.0.1
#     # For local testing, this will still point to localhost, but for Vercel, it needs adjustment
#     # Vercel will serve models/static assets from the root path
#     base_url = os.environ.get("VERCEL_URL", "http://127.0.0.1:8000")
    
#     # We strip 'http://' and replace it with 'https://' if deployed
#     if "vercel" in base_url and not base_url.startswith("https://"):
#         base_url = f"https://{base_url}"
        
#     # The Vercel function route is typically /api/... but static files are served from root
#     # Since your static mounts are /static and /models, we construct the path like this:
    
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
#     print(f"Whisper (audio): {'✅' if OPENAI_API_KEY else '❌'}")
#     # Use 0.0.0.0 for broader local network access
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)

import os
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

import faiss
import numpy as np
import torch
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from dotenv import load_dotenv

# ============================
# ENV
# ============================
load_dotenv(".env.local")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ============================
# DATA PATHS (Serverless-friendly)
# ============================
TMP_DIR = "/tmp"
DATA_IMAGES_DIR = os.path.join(TMP_DIR, "images")
MODELS_DIR = os.path.join(TMP_DIR, "models")
os.makedirs(DATA_IMAGES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

IMAGE_INDEX_PATH = os.path.join(TMP_DIR, "image_index.faiss")
TEXT_INDEX_PATH = os.path.join(TMP_DIR, "text_index.faiss")
ID_MAP_PATH = os.path.join(TMP_DIR, "id_map.npy")
CLEAN_PRODUCTS_PATH = os.path.join(TMP_DIR, "clean_products.json")

# ============================
# FASTAPI
# ============================
app = FastAPI(title="Multimodal Search")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ============================
# LOAD INDEXES + DATA
# ============================
image_index = safe_load_faiss(IMAGE_INDEX_PATH)
text_index = safe_load_faiss(TEXT_INDEX_PATH)
id_map = safe_load_npy(ID_MAP_PATH)
products = safe_load_json(CLEAN_PRODUCTS_PATH)

# ============================
# CLIP MODEL
# ============================
clip_model = None
clip_processor = None

def get_clip():
    global clip_model, clip_processor
    if clip_model is None:
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        clip_model.eval()
    return clip_model, clip_processor

# Preload CLIP once at cold start
get_clip()

# ============================
# UTILITY FUNCTIONS
# ============================
COMMON_COLORS = [
    "red", "blue", "green", "yellow", "black", "white", "brown", "grey", "pink",
    "purple", "orange", "beige", "navy", "burgundy", "maroon", "tan"
]

def detect_color_from_image(image_path: str) -> Optional[str]:
    try:
        img = Image.open(image_path).convert('RGB').resize((100, 100))
        pixels = np.array(img).reshape(-1, 3)
        avg_color = np.mean(pixels, axis=0)
        r, g, b = avg_color
        if max(r,g,b)<80: return "black"
        if min(r,g,b)>200: return "white"
        if r>g+30 and r>b+30: return "red"
        if g>r+30 and g>b+30: return "green"
        if b>r+30 and b>g+30: return "blue"
        return None
    except:
        return None

def product_matches_color(product: Dict, color: str) -> bool:
    if not color: return True
    name = product.get("productDisplayName","").lower()
    prod_color = product.get("color","").lower()
    return color in name or color in prod_color

def cosine_to_percent(score):
    return float((score + 1.0)/2.0)

def search_with_embedding(embedding, index, k=20, color_filter=None):
    if index is None or id_map is None: return []
    distances, indices = index.search(embedding, k*5)
    results=[]
    for dist, idx in zip(distances[0], indices[0]):
        if idx<0: continue
        product_id = int(id_map[int(idx)])
        p = products.get(product_id)
        if not p: continue
        score = cosine_to_percent(dist)
        if color_filter and not product_matches_color(p,color_filter): continue
        results.append({"id":product_id,"name":p.get("productDisplayName"),"category":p.get("masterCategory"),"subCategory":p.get("subCategory"),"image":p.get("image_path"),"color":p.get("color"),"score":score})
        if len(results)>=k*2: break
    return sorted(results,key=lambda x:x["score"],reverse=True)[:k]

# ============================
# SEARCH ENDPOINT
# ============================
@app.post("/search/intelligent")
async def intelligent_search(query: str = Form(""), image: UploadFile = File(None), top_k: int = Form(10)):
    modality_embeddings=[]
    color_filter=None
    
    # IMAGE EMBEDDING
    if image:
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp_img.write(await image.read())
        tmp_img.close()
        clip_model, clip_processor = get_clip()
        with torch.no_grad():
            pil_img = Image.open(tmp_img.name).convert("RGB")
            inputs = clip_processor(images=pil_img, return_tensors="pt").to(device)
            img_emb = clip_model.get_image_features(**inputs)
            img_emb = img_emb.cpu().numpy()
            img_emb /= np.linalg.norm(img_emb, axis=1, keepdims=True)
        modality_embeddings.append(img_emb[0])
        color_filter = detect_color_from_image(tmp_img.name)
        os.remove(tmp_img.name)
    
    # TEXT EMBEDDING
    if query.strip():
        clip_model, clip_processor = get_clip()
        with torch.no_grad():
            txt_inputs = clip_processor(text=[query], return_tensors="pt", padding=True, truncation=True).to(device)
            txt_emb = clip_model.get_text_features(**txt_inputs)
            txt_emb = txt_emb.cpu().numpy()
            txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)
        modality_embeddings.append(txt_emb[0])
    
    if not modality_embeddings:
        return JSONResponse(status_code=400, content={"error":"No input provided"})
    
    final_embedding = np.mean(modality_embeddings, axis=0, keepdims=True)
    final_embedding /= np.linalg.norm(final_embedding, axis=1, keepdims=True)
    final_embedding = final_embedding.astype("float32")
    
    index = image_index if image and not query else text_index
    results = search_with_embedding(final_embedding, index, k=top_k, color_filter=color_filter)
    
    return {
        "query": query,
        "interpreted_query": query,
        "accurate_results": results,
        "related_results": [],
        "color_filter": color_filter
    }

@app.get("/")
def root():
    return {"message":"Multimodal Search API Ready"}

