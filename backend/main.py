"""
Smart Furniture Search API
Run with: python main.py

Setup (one time):
    pip install openai-whisper

Voice uses openai-whisper (free, local, no API key, works on Windows).
All models load lazily on first use. Server starts in under 2 seconds.
"""

import os
import json
import tempfile
import asyncio
import threading
import traceback
from pathlib import Path
from typing import Optional

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

# ============================================================
# App
# ============================================================

app = FastAPI(title="Multimodal Furniture Search", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


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
    global _products, _image_index, _text_index, _id_map, _data_ready, _data_error
    with _data_lock:
        if _data_ready:
            return True
        try:
            print("[DATA] Loading...")
            with open(PRODUCTS_PATH, encoding="utf-8") as f:
                _products = json.load(f)
            _image_index = faiss.read_index(str(IMAGE_INDEX_PATH))
            _text_index  = faiss.read_index(str(TEXT_INDEX_PATH))
            _id_map      = np.load(str(ID_MAP_PATH))
            _data_ready  = True
            print(f"[DATA] Ready — {len(_products)} products")
            return True
        except Exception as e:
            _data_error = str(e)
            print(f"[DATA] ERROR: {e}")
            return False


def _ensure_clip():
    global _clip_model, _clip_proc, _clip_ready, _clip_error
    with _clip_lock:
        if _clip_ready:
            return True
        try:
            print("[CLIP] Loading... (~30s first time)")
            from transformers import CLIPModel, CLIPProcessor
            _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            _clip_model.to(DEVICE).eval()
            _clip_proc  = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            _clip_ready = True
            print("[CLIP] Ready")
            return True
        except Exception as e:
            _clip_error = str(e)
            print(f"[CLIP] ERROR: {e}")
            traceback.print_exc()
            return False


def _ensure_whisper():
    """
    Uses openai-whisper (original package, NOT faster-whisper).
    Install: pip install openai-whisper
    Works on Windows without symlink/cache issues.
    """
    global _whisper_model, _whisper_ready, _whisper_error
    with _whisper_lock:
        if _whisper_ready:
            return True
        try:
            print("[WHISPER] Loading openai-whisper tiny...")
            import whisper  # openai-whisper package
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

# ============================================================
# Color helpers
# ============================================================

_COLORS = {
    "black":    ["black", "noir"],
    "white":    ["white", "blanc"],
    "red":      ["red", "rouge"],
    "green":    ["green", "vert"],
    "blue":     ["blue", "bleu"],
    "yellow":   ["yellow", "jaune"],
    "brown":    ["brown", "marron"],
    "gray":     ["gray", "grey", "gris"],
    "orange":   ["orange"],
    "pink":     ["pink", "rose"],
    "purple":   ["purple", "violet"],
    "beige":    ["beige", "tan", "cream"],
    "navy":     ["navy"],
    "burgundy": ["burgundy", "wine"],
}


def _extract_color(text: str) -> Optional[str]:
    if not text:
        return None
    for word in text.lower().split():
        for color, variants in _COLORS.items():
            if word in variants or any(v in word for v in variants):
                return color
    return None


def _matches_color(product: dict, color: str) -> bool:
    if not color:
        return True
    c    = color.lower()
    pclr = product.get("baseColour", "").lower()
    pnam = product.get("productDisplayName", "").lower()
    if c == pclr or c in pclr or c in pnam:
        return True
    if c in ["gray", "grey"]:
        return "gray" in pclr or "grey" in pclr or "gray" in pnam or "grey" in pnam
    opp = {"black": ["white","light","cream"], "white": ["black","dark"],
           "red": ["blue","green"], "blue": ["red","orange"]}
    if c in opp and any(o in pclr or o in pnam for o in opp[c]):
        return False
    return False


def _make_result(product: dict, score: float) -> dict:
    img  = product.get("image_path", "")
    glb  = product.get("glb_path")
    has3 = product.get("has_3d_model", False)
    return {
        "id":           product["id"],
        "name":         product["productDisplayName"],
        "category":     product.get("masterCategory", "Furniture"),
        "subCategory":  product.get("subCategory", ""),
        "image":        img,
        "color":        product.get("baseColour", ""),
        "score":        float(max(0.0, min(1.0, score))),
        "has_3d_model": has3,
        "image_url":    f"{BASE_URL}/static/images/{img}" if img else "",
        "model_url":    f"{BASE_URL}/static/models/{glb}" if (has3 and glb) else None,
    }

# ============================================================
# Search & transcribe (blocking, called via run_in_executor)
# ============================================================

def _do_search(query: str, img_path: Optional[str],
               color: Optional[str], top_k: int) -> list:
    vecs = []
    if query.strip():
        inp = _clip_proc(text=[query], return_tensors="pt",
                         padding=True, truncation=True, max_length=77).to(DEVICE)
        with torch.no_grad():
            v = _clip_model.get_text_features(**inp).cpu().numpy().astype("float32")
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        vecs.append(v[0])

    if img_path:
        img = Image.open(img_path).convert("RGB")
        inp = _clip_proc(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            v = _clip_model.get_image_features(**inp).cpu().numpy().astype("float32")
        v /= np.linalg.norm(v, axis=1, keepdims=True)
        vecs.append(v[0])

    if not vecs:
        return []

    combined = np.mean(vecs, axis=0, keepdims=True).astype("float32")
    combined /= np.linalg.norm(combined, axis=1, keepdims=True)
    index = _image_index if (img_path and not query.strip()) else _text_index
    dists, idxs = index.search(combined, top_k * 6)

    results = []
    for dist, idx in zip(dists[0], idxs[0]):
        if idx < 0:
            continue
        product = _products[int(_id_map[int(idx)])]
        if color and not _matches_color(product, color):
            continue
        results.append(_make_result(product, dist))
        if len(results) >= top_k:
            break
    return sorted(results, key=lambda x: x["score"], reverse=True)


def _do_transcribe(path: str) -> str:
    """
    Read a WAV file using Python stdlib (no ffmpeg, no pydub needed).
    The browser converts audio to 16kHz mono WAV before sending.
    """
    if os.path.getsize(path) < 200:
        return ""
    if not _whisper_model:
        return ""
    try:
        import wave, struct
        with wave.open(path, "rb") as wf:
            n_channels  = wf.getnchannels()
            sampwidth   = wf.getsampwidth()
            framerate   = wf.getframerate()
            n_frames    = wf.getnframes()
            raw         = wf.readframes(n_frames)

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

        # Resample to 16000 Hz if needed (browser already does this, just in case)
        if framerate != 16000:
            factor  = 16000 / framerate
            new_len = int(len(samples) * factor)
            indices = np.linspace(0, len(samples) - 1, new_len)
            samples = np.interp(indices, np.arange(len(samples)), samples).astype(np.float32)

        result = _whisper_model.transcribe(samples, language="en", fp16=False)
        text   = result["text"].strip()
        print(f"[WHISPER] Heard: '{text}'")
        return text

    except Exception as e:
        print(f"[WHISPER] error: {e}")
        traceback.print_exc()
        return ""

def root():
    return {"status": "online", "data_ready": _data_ready,
            "clip_ready": _clip_ready, "whisper_ready": _whisper_ready,
            "data_error": _data_error, "clip_error": _clip_error,
            "whisper_error": _whisper_error,
            "products": len(_products) if _products else 0}


@app.get("/health")
def health():
    return {"status": "healthy" if (_data_ready and _clip_ready) else "loading",
            "data_ready": _data_ready, "clip_ready": _clip_ready,
            "whisper_ready": _whisper_ready,
            "data_error": _data_error, "clip_error": _clip_error,
            "whisper_error": _whisper_error,
            "products": len(_products) if _products else 0}


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    loop = asyncio.get_event_loop()
    if not _data_ready:
        await loop.run_in_executor(None, _ensure_data)
    if not _data_ready:
        raise HTTPException(503, detail=f"Data error: {_data_error}")
    if product_id < 0 or product_id >= len(_products):
        raise HTTPException(404, detail="Product not found")
    p    = _products[product_id]
    glb  = p.get("glb_path")
    has3 = p.get("has_3d_model", False)
    img  = p.get("image_path", "")
    murl = f"{BASE_URL}/static/models/{glb}" if (has3 and glb) else None
    return {
        "id": p["id"], "name": p["productDisplayName"],
        "category": p.get("masterCategory", "Furniture"),
        "subCategory": p.get("subCategory", ""),
        "image": img, "color": p.get("baseColour", ""),
        "has_3d_model": has3, "glb_path": glb or "",
        "image_url": f"{BASE_URL}/static/images/{img}" if img else "",
        "model_url": murl,
        "model_exists": (MODELS_DIR / glb).exists() if murl else False,
    }


@app.post("/search/intelligent")
async def search(
    query: Optional[str] = Form(""),
    file:  Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    top_k: int = Form(10),
):
    loop = asyncio.get_event_loop()

    # Ensure data
    if not _data_ready:
        await loop.run_in_executor(None, _ensure_data)
    if not _data_ready:
        raise HTTPException(503, detail=f"Data error: {_data_error}")

    # Ensure CLIP
    if not _clip_ready:
        print("[CLIP] First request — loading now (~30s)...")
        ok = await loop.run_in_executor(None, _ensure_clip)
        if not ok:
            raise HTTPException(500, detail=f"CLIP failed: {_clip_error}")

    typed_query = (query or "").strip()
    voice_query = ""
    voice_error = None
    tmp_audio   = None
    tmp_img     = None

    # Voice
    if audio:
        try:
            data = await audio.read()
            print(f"[VOICE] {len(data)} bytes")

            if not _whisper_ready:
                print("[WHISPER] Loading for first voice request...")
                await loop.run_in_executor(None, _ensure_whisper)

            if not _whisper_ready:
                voice_error = _whisper_error or "Whisper unavailable"
            elif len(data) < 200:
                voice_error = "Audio too short — hold mic button longer"
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(data)
                    tmp_audio = f.name
                voice_query = await loop.run_in_executor(None, _do_transcribe, tmp_audio)
                if not voice_query:
                    voice_error = "Could not understand audio"
                else:
                    # Validate the transcription is a plausible search query
                    # Reject if it looks like background TV/noise (too long, no furniture words)
                    furniture_words = [
                        "sofa","couch","chair","table","desk","bed","shelf","cabinet",
                        "wardrobe","lamp","rug","curtain","drawer","bookcase","stool",
                        "bench","ottoman","dresser","mirror","furniture","wooden","leather",
                        "black","white","brown","gray","grey","red","blue","green","navy",
                        "want","need","find","search","show","looking","like","similar",
                        "buy","modern","vintage","small","large","dark","light","cheap"
                    ]
                    words      = voice_query.lower().split()
                    has_intent = any(w in " ".join(words) for w in furniture_words)
                    too_long   = len(words) > 15  # Real searches are short
                    if not has_intent and too_long:
                        print(f"[VOICE] Rejected as background noise: {repr(voice_query)}")
                        voice_error = f"Heard background noise, not a search query. Please speak clearly."
                        voice_query = ""
                    else:
                        print(f"[VOICE] Accepted: {repr(voice_query)}")
        except Exception as e:
            voice_error = str(e)
            print(f"[VOICE] Error: {e}")
        finally:
            if tmp_audio and os.path.exists(tmp_audio):
                os.remove(tmp_audio)

    # Merge
    color_filter = _extract_color(voice_query) or _extract_color(typed_query)
    final_query  = (f"{voice_query} {typed_query}".strip()
                    if voice_query and typed_query else voice_query or typed_query)

    # ── Spell correction for common furniture terms ──────────────
    corrections = {
        "wardope": "wardrobe", "wardorbe": "wardrobe", "wardrob": "wardrobe",
        "wardrop": "wardrobe", "wardobe": "wardrobe",
        "coatch": "couch", "sopha": "sofa", "soaf": "sofa",
        "tabel": "table",  "tablee": "table",
        "cahir": "chair",  "chiar": "chair", "chare": "chair",
        "bedd": "bed",     "beed": "bed",
        "shelff": "shelf", "shef": "shelf",
        "lmap": "lamp",    "lapm": "lamp",
        "cabnet": "cabinet", "cabenit": "cabinet",
        "dresers": "dresser", "draser": "dresser",
        "otoman": "ottoman", "ottaman": "ottoman",
        "benchh": "bench",
        "mirroe": "mirror", "miror": "mirror",
        "curtan": "curtain", "courtain": "curtain",
    }
    corrected_query = None
    if final_query:
        words    = final_query.lower().split()
        new_words = [corrections.get(w, w) for w in words]
        if new_words != words:
            corrected_query = " ".join(new_words)
            print(f"[SEARCH] Spell corrected: {repr(final_query)} -> {repr(corrected_query)}")
            final_query = corrected_query

    print(f"[SEARCH] typed='{typed_query}' voice='{voice_query}' "
          f"final='{final_query}' color={color_filter}")

    # Image
    img_file = file or image
    if img_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(await img_file.read())
            tmp_img = f.name

    if not final_query and not tmp_img:
        return _empty(typed_query, voice_query, voice_error,
                      "Please provide text, image, or voice")

    try:
        results = await loop.run_in_executor(
            None, _do_search, final_query, tmp_img, color_filter, top_k)
    except Exception as e:
        print(f"[SEARCH] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(500, detail=f"Search failed: {e}")
    finally:
        if tmp_img and os.path.exists(tmp_img):
            os.remove(tmp_img)

    parts = (["text"] if typed_query else []) + \
            (["image"] if tmp_img else []) + \
            (["voice"] if voice_query else [])
    mode      = " + ".join(parts) if parts else "unknown"
    color_str = f" {color_filter}" if color_filter else ""

    return {
        "query": final_query, "interpreted_query": final_query,
        "typed_query": typed_query, "voice_query": voice_query,
        "voice_error": voice_error,
        "accurate_results": results, "related_results": [],
        "total_results": len(results), "color_filter": color_filter,
        "search_mode": mode,
        "ai_summary": f"Found {len(results)}{color_str} items [{mode}]",
    }


def _empty(typed, voice, verr, msg):
    return {"query": "", "interpreted_query": "",
            "typed_query": typed, "voice_query": voice, "voice_error": verr,
            "accurate_results": [], "related_results": [],
            "total_results": 0, "color_filter": None,
            "search_mode": "none", "ai_summary": msg}


if __name__ == "__main__":
    import uvicorn
    print("\nStarting — http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, workers=1)