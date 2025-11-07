# """
# FREE LLM-Powered Multimodal Search
# Uses: Gemini (vision) + Groq (reasoning) - Both FREE!

# Setup:
# 1. Get Gemini key: https://aistudio.google.com/app/apikey (no credit card!)
# 2. Get Groq key: https://console.groq.com/ (no credit card!)
# 3. Set environment variables:
#    export GEMINI_API_KEY="your-key"
#    export GROQ_API_KEY="your-key"
# """

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

# Load .env.local file
load_dotenv('.env.local')

# Try importing Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. Run: pip install google-generativeai")

# ============================
# CONFIG
# ============================
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

DATA_IMAGES_DIR = "data/images"
CLEAN_PRODUCTS_PATH = "data/clean_products.json"
IMAGE_INDEX_PATH = "data/image_index.faiss"
TEXT_INDEX_PATH = "data/text_index.faiss"
ID_MAP_PATH = "data/id_map.npy"

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Configure Gemini
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini configured")
else:
    print("⚠️ Gemini not configured (set GEMINI_API_KEY)")

# ============================
# APP SETUP
# ============================
app = FastAPI(title="Free LLM-Powered Search (Gemini + Groq)")
app.mount("/static", StaticFiles(directory=DATA_IMAGES_DIR), name="static")
app.mount("/models", StaticFiles(directory="data/models"), name="models")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_grad_enabled(False)

# ============================
# LOAD DATA
# ============================
print("Loading FAISS indexes...")
image_index = faiss.read_index(IMAGE_INDEX_PATH)
text_index = faiss.read_index(TEXT_INDEX_PATH)
id_map = np.load(ID_MAP_PATH)

print("Loading product metadata...")
with open(CLEAN_PRODUCTS_PATH, "r", encoding="utf-8") as f:
    products = {int(p["id"]): p for p in json.load(f)}

CATEGORIES = list(set([p.get("subCategory", "") for p in products.values() if p.get("subCategory")]))

# ============================
# CONVERSATION MEMORY
# ============================
conversation_sessions = {}

class ConversationSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.context = {
            "previous_query": None,
            "previous_image": None,
            "previous_results": [],
        }
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
    
    def get_history_string(self) -> str:
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.messages[-4:]])

# ============================
# MODELS
# ============================
clip_model = None
clip_processor = None

def get_clip():
    global clip_model, clip_processor
    if clip_model is None:
        print("Loading CLIP model...")
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        clip_model.eval()
    return clip_model, clip_processor

# ============================
# FREE LLM FUNCTIONS
# ============================
def call_groq(messages: List[Dict], temperature: float = 0.7) -> str:
    if not GROQ_API_KEY:
        return "⚠️ Groq API key not set"
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"❌ Groq error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"❌ Groq failed: {e}")
        return ""

def analyze_image_gemini(image_path: str) -> str:
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return "⚠️ Gemini not configured"
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(image_path)

        prompt = """Analyze this furniture image. Describe in 2-3 sentences:
- Type of furniture (chair, table, sofa, etc.)
- Style (modern, vintage, rustic, etc.)
- Color and material
- Notable design features
Be specific and concise."""

        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini image analysis failed: {e}")
        return ""

def interpret_query(session: ConversationSession, current_query: str, image_description: Optional[str] = None) -> Dict:
    context_parts = []
    if session.context["previous_query"]:
        context_parts.append(f"Previous query: {session.context['previous_query']}")
    if session.context["previous_image"]:
        context_parts.append(f"Previous image: {session.context['previous_image']}")
    if image_description:
        context_parts.append(f"Current image: {image_description}")
    if session.context["previous_results"]:
        top = session.context["previous_results"][:3]
        context_parts.append(f"Previous results: {', '.join([r['name'] for r in top])}")

    context_str = "\n".join(context_parts) if context_parts else "No previous context"

    system_prompt = f"""You are a furniture shopping assistant.

Available categories: {', '.join(CATEGORIES[:20])}

Analyze the user's query and return JSON:
{{
    "search_query": "optimized keywords for search",
    "category": "specific category or null",
    "intent": "search/refine/similar/compare",
    "explanation": "brief interpretation"
}}

Handle phrases like:
- "find similar" → use previous context
- "add patterns" → modify previous search
- "but in blue" → add color filter

Context:
{context_str}

Current query: "{current_query}"

Return only valid JSON."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Interpret: {current_query}"}
    ]

    response = call_groq(messages, temperature=0.3)
    if not response:
        return {"search_query": current_query, "category": None, "intent": "search", "explanation": "Direct search"}

    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except:
        pass

    return {"search_query": current_query, "category": None, "intent": "search", "explanation": "Direct search"}

def generate_summary(query: str, results: List[Dict], interpretation: Dict) -> str:
    if not results:
        prompt = f"""User searched for: "{query}"

No exact matches found. Suggest 2–3 related products available in the dataset 
(e.g. similar materials, colors, or categories). Be specific and helpful."""
        messages = [
            {"role": "system", "content": "You are a helpful furniture shopping assistant."},
            {"role": "user", "content": prompt}
        ]
        return call_groq(messages, temperature=0.8)

    results_text = "\n".join([
        f"- {r['name']} ({r['subCategory']}) - {r['score']*100:.0f}% match"
        for r in results[:5]
    ])
    prompt = f"""User searched for: "{query}"
Interpretation: {interpretation.get('explanation', '')}

Top results:
{results_text}

Provide a 2–3 sentence summary that highlights best matches and suggests refinements if needed."""
    
    messages = [
        {"role": "system", "content": "You are a helpful furniture shopping assistant."},
        {"role": "user", "content": prompt}
    ]
    return call_groq(messages, temperature=0.7)

# ============================
# SEARCH HELPERS
# ============================
def cosine_similarity_to_percentage(distance):
    return max(0.0, 1.0 - (distance ** 2) / 2.0)

def get_top_k_results(embeddings, index, k=10, category_filter=None):
    distances, indices = index.search(embeddings, k * 5)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:
            continue
        product_id = int(id_map[int(idx)])
        p = products.get(product_id, {})
        if category_filter and p.get("subCategory") != category_filter:
            continue
        sim = cosine_similarity_to_percentage(dist)
        results.append({
            "id": product_id,
            "name": p.get("productDisplayName"),
            "category": p.get("masterCategory"),
            "subCategory": p.get("subCategory"),
            "image": p.get("image_path"),
            "score": float(sim)
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)[:k]

# ============================
# ROUTES
# ============================
@app.get("/")
def root():
    return {
        "message": "Free LLM-Powered Search API",
        "gemini": "✅" if (GEMINI_AVAILABLE and GEMINI_API_KEY) else "❌",
        "groq": "✅" if GROQ_API_KEY else "❌"
    }

@app.post("/search/intelligent")
async def intelligent_search(
    file: UploadFile = File(None),
    query: str = Form(""),
    session_id: str = Form("default"),
    top_k: int = Form(10)
):
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = ConversationSession(session_id)
    session = conversation_sessions[session_id]
    session.add_message("user", query or "uploaded image")

    image_description = None
    if file and GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(await file.read())
            tmp.close()
            image_description = analyze_image_gemini(tmp.name)
            os.remove(tmp.name)
            print(f"🖼️ Gemini: {image_description}")
            session.context["previous_image"] = image_description
        except Exception as e:
            print(f"⚠️ Image analysis error: {e}")

    interpretation = interpret_query(session, query, image_description)
    print(f"🧠 Groq: {interpretation}")

    search_text = interpretation.get("search_query", query)
    if image_description:
        search_text = f"{search_text} {image_description}"

    clip_model, clip_processor = get_clip()
    with torch.no_grad():
        inputs = clip_processor(text=[search_text], return_tensors="pt").to(device)
        txt_emb = clip_model.get_text_features(**inputs)
    txt_emb = txt_emb.cpu().numpy()
    txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)

    category = interpretation.get("category")
    results = get_top_k_results(
        txt_emb,
        text_index,
        top_k,
        category_filter=None if category in [None, "", "misc"] else category
    )

    session.context["previous_query"] = query
    session.context["previous_results"] = results

    ai_summary = generate_summary(query, results, interpretation)

    return {
        "query": query,
        "interpreted_query": search_text,
        "interpretation": interpretation,
        "results": results,
        "ai_summary": ai_summary,
        "llm_status": {
            "vision": "gemini" if (GEMINI_AVAILABLE and image_description) else "none",
            "reasoning": "groq" if GROQ_API_KEY else "none"
        }
    }

@app.post("/conversation/reset")
async def reset_conversation(session_id: str = Form("default")):
    if session_id in conversation_sessions:
        del conversation_sessions[session_id]
    return {"message": "Conversation reset"}

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
    print("\n" + "="*60)
    print("FREE LLM-POWERED SEARCH")
    print("="*60)
    print(f"Gemini (vision): {'✅ Ready' if (GEMINI_AVAILABLE and GEMINI_API_KEY) else '❌ Not configured'}")
    print(f"Groq (reasoning): {'✅ Ready' if GROQ_API_KEY else '❌ Not configured'}")
    print("="*60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
