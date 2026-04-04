# frameworks/interfaces.py
# Fully lazy implementation to bypass environmental import hangs

class OllamaFramework:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    async def generate(self, prompt: str, model: str = "llama3"):
        """Generate text using local Ollama LLM"""
        import requests
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=10
            )
            return response.json().get("response", "")
        except Exception as e:
            print(f"[Ollama] Error: {e}")
            return ""

    async def vision_reasoning(self, prompt: str, image_path: str, model: str = "llava"):
        """Perform visual reasoning using local Ollama VLM (LLaVA)"""
        import os
        import base64
        import requests
        if not image_path or not os.path.exists(image_path):
            return ""
        try:
            with open(image_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "images": [img_base64],
                    "stream": False
                },
                timeout=20
            )
            return response.json().get("response", "")
        except Exception as e:
            print(f"[Ollama Vision] Error: {e}")
            return ""

class ModelFramework:
    def __init__(self, model_name='google/siglip-base-patch16-224', device=None):
        print(f"DEBUG: ModelFramework __init__ started for {model_name}")
        import torch
        from transformers import AutoModel, AutoProcessor
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[SigLIP] Loading {model_name} on {self.device}...")
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model.eval()

    async def get_embeddings(self, text: str = None, image_path: str = None):
        """Returns unified embeddings using SigLIP via Transformers"""
        import torch
        import os
        import numpy as np
        from PIL import Image
        vecs = []
        with torch.no_grad():
            if text and text.strip():
                inputs = self.processor(text=[text], padding="max_length", return_tensors="pt").to(self.device)
                text_features = self.model.get_text_features(**inputs)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                vecs.append(text_features.cpu().numpy().astype("float32"))

            if image_path and os.path.exists(image_path):
                image = Image.open(image_path).convert("RGB")
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                image_features = self.model.get_image_features(**inputs)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                vecs.append(image_features.cpu().numpy().astype("float32"))

        if not vecs:
            return None
            
        combined = np.mean(vecs, axis=0)
        combined /= np.linalg.norm(combined, axis=1, keepdims=True)
        return combined

class WhisperFramework:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        from faster_whisper import WhisperModel
        print(f"[Whisper] Loading {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using faster-whisper locally"""
        import os
        if not audio_path or not os.path.exists(audio_path):
            return ""
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        text = "".join([segment.text for segment in segments]).strip()
        return text

class DatabaseFramework:
    def __init__(self, products_path, chroma_path=None, index_path=None, id_map_path=None):
        import faiss
        import json
        import os
        import numpy as np
        self.products_path = products_path
        self.chroma_path = chroma_path
        
        # Use provided paths or fall back to defaults near products_path
        p_dir = os.path.dirname(products_path)
        self.index_path = index_path or os.path.join(p_dir, "image_index.faiss")
        self.id_map_path = id_map_path or os.path.join(p_dir, "id_map.npy")
        
        print(f"[DB] Loading indices from {self.index_path}...")
        with open(products_path, encoding="utf-8") as f:
            self.products = json.load(f)
        self.index = faiss.read_index(str(self.index_path))
        self.id_map = np.load(str(self.id_map_path))

    async def search_vectors(self, vectors, top_k: int, color: str = None):
        """Search existing FAISS index (to be migrated to ChromaDB later)"""
        import numpy as np
        if vectors is None:
            return []
            
        dists, idxs = self.index.search(vectors, top_k * 5)
        results = []
        for dist, idx in zip(dists[0], idxs[0]):
            if idx < 0: continue
            product_idx = int(self.id_map[int(idx)])
            product = self.products[product_idx]
            
            # Basic color filter logic (migrated from main.py)
            if color and color.lower() not in product.get("baseColour", "").lower():
                continue
                
            results.append({
                "product": product,
                "score": float(dist)
            })
            if len(results) >= top_k:
                break
        return results
