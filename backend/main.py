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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

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
app = FastAPI(title="Free LLM Multimodal Search (Gemini + Groq)")
app.mount("/static", StaticFiles(directory=DATA_IMAGES_DIR), name="static")
app.mount("/models", StaticFiles(directory="data/models"), name="models")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

# ============================
# SAFE LOADERS
# ============================
def safe_load_faiss(path):
    if os.path.exists(path):
        return faiss.read_index(path)
    print(f"⚠️ FAISS index not found: {path}")
    return None

def safe_load_npy(path):
    if os.path.exists(path):
        return np.load(path)
    print(f"⚠️ NPY file not found: {path}")
    return None

def safe_load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {int(p["id"]): p for p in json.load(f)}
    print(f"⚠️ JSON file not found: {path}")
    return {}

print("📦 Loading FAISS indexes and metadata...")
image_index = safe_load_faiss(IMAGE_INDEX_PATH)
text_index = safe_load_faiss(TEXT_INDEX_PATH)
id_map = safe_load_npy(ID_MAP_PATH)
products = safe_load_json(CLEAN_PRODUCTS_PATH)

# Analyze what's actually in the dataset
DATASET_CATEGORIES = list(set(p.get("masterCategory", "") for p in products.values() if p.get("masterCategory")))
DATASET_SUBCATEGORIES = list(set(p.get("subCategory", "") for p in products.values() if p.get("subCategory")))

print(f"📊 Dataset contains: {DATASET_CATEGORIES}")
print(f"📊 Subcategories: {DATASET_SUBCATEGORIES[:10]}...")  # Show first 10

# ============================
# CLIP MODEL LOADING
# ============================
clip_model = None
clip_processor = None

def get_clip():
    global clip_model, clip_processor
    if clip_model is None or clip_processor is None:
        try:
            print("🔠 Loading CLIP model...")
            clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
            clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            clip_model.eval()
        except Exception as e:
            print(f"❌ Failed to load CLIP model: {e}")
            clip_model = None
            clip_processor = None
    return clip_model, clip_processor

# ============================
# LLM HELPERS (GROQ + GEMINI)
# ============================
def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
    if not GROQ_API_KEY:
        return "⚠️ Groq API key not set"
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 800,
            },
            timeout=30,
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        print(f"❌ Groq error: {res.status_code}")
        return ""
    except Exception as e:
        print(f"❌ Groq failed: {e}")
        return ""

def analyze_image_gemini(image_path: str) -> str:
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return ""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        img = Image.open(image_path)
        prompt = """Describe this furniture image in detail:
- Furniture type (chair, table, etc.)
- Color and material
- Style (modern, rustic, etc.)
Keep it short."""
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini image analysis failed: {e}")
        return ""

# ============================
# QUERY VALIDATION & MAPPING
# ============================
def validate_and_map_query(query: str) -> Dict[str, any]:
    """
    Validates if the query matches the dataset domain and maps it to furniture if needed.
    Returns: {
        "is_valid": bool,
        "mapped_query": str,
        "explanation": str,
        "original_query": str
    }
    """
    if not GROQ_API_KEY:
        return {
            "is_valid": True,
            "mapped_query": query,
            "explanation": "",
            "original_query": query
        }
    
    try:
        dataset_info = f"Available categories: {', '.join(DATASET_CATEGORIES)}\nSubcategories: {', '.join(DATASET_SUBCATEGORIES[:20])}"
        
        messages = [
            {"role": "system", "content": f"""You are a smart query validator for a furniture search engine.

Dataset contains ONLY: {', '.join(DATASET_CATEGORIES)}

Your tasks:
1. If the query is about furniture → return it as-is or improve it
2. If the query is about clothing/electronics/etc → map it to similar FURNITURE or explain why no match exists

Response format (JSON only):
{{
    "is_valid": true/false,
    "mapped_query": "optimized query here",
    "explanation": "brief explanation"
}}

Examples:
- "red jacket" → {{"is_valid": false, "mapped_query": "", "explanation": "We only have furniture like wardrobes, not clothing."}}
- "wooden wardrobe" → {{"is_valid": true, "mapped_query": "wooden wardrobe cabinet", "explanation": ""}}
- "blue sofa" → {{"is_valid": true, "mapped_query": "blue sofa couch", "explanation": ""}}
"""},
            {"role": "user", "content": f"Query: '{query}'\n\n{dataset_info}"}
        ]
        
        response = call_groq(messages, temperature=0.3)
        
        # Parse JSON response
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            result["original_query"] = query
            return result
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse LLM response: {response}")
            return {
                "is_valid": True,
                "mapped_query": query,
                "explanation": "",
                "original_query": query
            }
            
    except Exception as e:
        print(f"⚠️ Query validation failed: {e}")
        return {
            "is_valid": True,
            "mapped_query": query,
            "explanation": "",
            "original_query": query
        }

# ============================
# QUERY EXPANSION WITH TOKEN LIMIT
# ============================
def expand_query_for_search(query: str, image_description: str = None) -> str:
    """
    Expands query while ensuring it stays within CLIP's 77 token limit.
    Returns a SHORT, keyword-focused query optimized for CLIP embedding.
    """
    if not GROQ_API_KEY:
        base = query.strip()
        if image_description:
            return f"{base} {image_description[:50]}"
        return base
    
    try:
        context = f"Original query: '{query}'"
        if image_description:
            context += f"\nImage shows: {image_description}"
        
        messages = [
            {"role": "system", "content": """You are a search query optimizer for furniture. Create SHORT, keyword-rich queries.

Rules:
1. Output ONLY 5-10 keywords maximum
2. Focus on: color, material, style, furniture type
3. NO sentences or explanations
4. Example: "red wardrobe" → "red wardrobe cabinet wooden door storage"
5. Keep under 15 words TOTAL"""},
            {"role": "user", "content": context},
        ]
        
        expanded = call_groq(messages, temperature=0.3)
        expanded = expanded.strip()[:50]
        expanded = expanded.replace('"', '').replace("'", '').strip()
        
        print(f"🔍 Query optimization: '{query}' → '{expanded}'")
        return expanded
        
    except Exception as e:
        print(f"⚠️ Query expansion failed: {e}")
        return query.strip()

# ============================
# SEARCH HELPERS
# ============================
def cosine_similarity_to_percentage(distance):
    return max(0.0, 1.0 - (distance ** 2) / 2.0)

def get_top_k_results(embeddings, index, k=10, category_filter=None):
    if index is None or id_map is None:
        return []
    distances, indices = index.search(embeddings, k * 5)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        product_id = int(id_map[int(idx)])
        p = products.get(product_id, {})
        if not p:
            continue
        if category_filter and p.get("subCategory") != category_filter:
            continue
        results.append({
            "id": product_id,
            "name": p.get("productDisplayName"),
            "category": p.get("masterCategory"),
            "subCategory": p.get("subCategory"),
            "image": p.get("image_path"),
            "score": float(cosine_similarity_to_percentage(dist)),
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

# ============================
# NATURAL LANGUAGE SUMMARY
# ============================
def generate_natural_summary(
    original_query: str,
    search_query: str,
    accurate_count: int,
    related_count: int,
    top_products: List[Dict],
    validation_result: Dict = None
) -> str:
    """
    Generates a friendly, conversational summary of search results.
    """
    if not GROQ_API_KEY:
        return f"Found {accurate_count} products matching your search for '{original_query}'."
    
    try:
        # Check if query was invalid
        if validation_result and not validation_result.get("is_valid"):
            explanation = validation_result.get("explanation", "")
            return f"I couldn't find what you're looking for. {explanation} Try searching for furniture items like 'wooden wardrobe', 'modern sofa', or 'glass coffee table'."
        
        # Build product context
        product_names = [p["name"] for p in top_products[:3]]
        product_context = ", ".join(product_names) if product_names else "various items"
        
        context = f"""User searched for: "{original_query}"
We used this search: "{search_query}"
Found {accurate_count} strong matches and {related_count} related items.
Top products include: {product_context}"""

        if validation_result and validation_result.get("mapped_query"):
            context += f"\nNote: Query was mapped from '{original_query}' to furniture domain"
        
        messages = [
            {"role": "system", "content": """You are a friendly furniture shopping assistant. Keep responses warm and helpful.

Guidelines:
- Be natural and enthusiastic about furniture
- Mention 1-2 specific products if available
- If few matches, suggest similar furniture items
- Keep it to 2-3 sentences
- Sound like a helpful store assistant"""},
            {"role": "user", "content": context}
        ]
        
        response = call_groq(messages, temperature=0.8)
        return response.strip() if response else f"Found {accurate_count} great furniture options for you!"
        
    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")
        return f"Found {accurate_count} products matching '{original_query}'."

# ============================
# MAIN SEARCH ENDPOINT
# ============================
@app.post("/search/intelligent")
async def intelligent_search(
    file: UploadFile = File(None),
    query: str = Form(""),
    top_k: int = Form(10),
    session_id: str = Form("default"),
):
    try:
        image_description = None

        # Image → Gemini
        if file and GEMINI_AVAILABLE and GEMINI_API_KEY:
            try:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(await file.read())
                tmp.close()
                image_description = analyze_image_gemini(tmp.name)
                os.remove(tmp.name)
                print(f"🖼️ Gemini detected: {image_description}")
            except Exception as e:
                print(f"⚠️ Image analysis error: {e}")

        # STEP 1: Validate and map query to dataset domain
        validation_result = validate_and_map_query(query)
        
        print(f"🔍 Validation: {validation_result}")
        
        # If query is invalid and no mapping possible, return early with explanation
        if not validation_result["is_valid"] and not validation_result["mapped_query"]:
            natural_response = generate_natural_summary(
                original_query=query,
                search_query="",
                accurate_count=0,
                related_count=0,
                top_products=[],
                validation_result=validation_result
            )
            
            return {
                "query": query,
                "interpreted_query": "",
                "ai_summary": natural_response,
                "accurate_results": [],
                "related_results": [],
                "total_found": 0,
                "validation": validation_result,
                "llm_status": {
                    "vision": "gemini" if image_description else "none",
                    "reasoning": "groq" if GROQ_API_KEY else "none",
                    "query_valid": False
                },
            }
        
        # Use mapped query if available, otherwise use original
        effective_query = validation_result["mapped_query"] if validation_result["mapped_query"] else query

        # STEP 2: Expand query for CLIP search
        search_query = expand_query_for_search(effective_query, image_description)
        
        print(f"🔍 Original: '{query}' | Effective: '{effective_query}' | Search: '{search_query}'")

        # Encode with CLIP
        clip_model, clip_processor = get_clip()
        if clip_model is None or clip_processor is None:
            return JSONResponse(status_code=500, content={"error": "CLIP model not loaded"})

        try:
            with torch.no_grad():
                inputs = clip_processor(
                    text=[search_query],
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=77
                ).to(device)
                txt_emb = clip_model.get_text_features(**inputs)
        except Exception as e:
            print(f"❌ CLIP encoding failed: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Text encoding failed", "details": str(e)}
            )

        txt_emb = txt_emb.cpu().numpy()
        txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)

        # Search
        results = get_top_k_results(txt_emb, text_index, k=top_k * 3)

        # Split groups
        accurate_results = [r for r in results if r["score"] >= 0.70]
        related_results = [r for r in results if 0.50 <= r["score"] < 0.70]

        if not accurate_results and related_results:
            accurate_results = related_results[:5]
            related_results = related_results[5:15]

        # Generate natural language summary
        natural_response = generate_natural_summary(
            original_query=query,
            search_query=search_query,
            accurate_count=len(accurate_results),
            related_count=len(related_results),
            top_products=accurate_results[:3],
            validation_result=validation_result
        )

        return {
            "query": query,
            "interpreted_query": search_query,
            "ai_summary": natural_response,
            "accurate_results": accurate_results[:top_k],
            "related_results": related_results[:top_k],
            "total_found": len(results),
            "validation": validation_result,
            "llm_status": {
                "vision": "gemini" if image_description else "none",
                "reasoning": "groq" if GROQ_API_KEY else "none",
                "query_valid": validation_result["is_valid"]
            },
        }

    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": "Search failed",
                "details": str(e),
                "query": query
            }
        )

# ============================
# MISC ROUTES
# ============================
@app.get("/")
def root():
    return {
        "message": "LLM Multimodal Search API Ready",
        "groq": bool(GROQ_API_KEY),
        "gemini": GEMINI_AVAILABLE,
        "dataset": {
            "categories": DATASET_CATEGORIES,
            "total_products": len(products)
        }
    }

@app.post("/conversation/reset")
async def reset_conversation(session_id: str = Form("default")):
    return {"message": f"Conversation {session_id} reset"}

@app.get("/products/{product_id}/ar-info")
async def get_ar_info(product_id: int):
    product = products.get(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    model_path = Path(f"data/models/{product_id}.glb")
    base_url = "http://localhost:8000"
    return {
        "product_id": product_id,
        "name": product.get("productDisplayName"),
        "model_url": f"{base_url}/models/{product_id}.glb" if model_path.exists() else None,
        "poster_url": f"{base_url}/static/{product.get('image_path')}",
        "ar_available": model_path.exists(),
    }

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
    print("🚀 FREE MULTIMODAL SEARCH SERVER")
    print("=" * 60)
    print(f"Gemini (vision): {'✅' if GEMINI_AVAILABLE and GEMINI_API_KEY else '❌'}")
    print(f"Groq (reasoning): {'✅' if GROQ_API_KEY else '❌'}")
    print(f"Dataset: {len(products)} products in {DATASET_CATEGORIES}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)