import json
import os
import torch
from transformers import AutoModel, AutoProcessor
from PIL import Image
import chromadb
from tqdm import tqdm
from pathlib import Path

# Paths
_base = Path(__file__).parent
DATA_DIR = _base / "data"
PRODUCTS_PATH = DATA_DIR / "clean_products.json"
IMAGES_DIR = DATA_DIR / "images"
CHROMA_PATH = DATA_DIR / "chroma_db"

# Settings
MODEL_NAME = 'google/siglip-base-patch16-224'
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def reindex():
    print(f"Starting Re-Indexing with {MODEL_NAME}...")
    
    # 1. Load Model
    model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model.eval()
    
    # 2. Setup Chroma
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(name="furniture_products")
    
    # 3. Load Products
    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        products = json.load(f)
    
    # 4. Process
    for p in tqdm(products):
        pid = str(p["id"])
        image_name = p.get("image_path")
        image_path = IMAGES_DIR / image_name if image_name else None
        
        # Get Image Embedding
        image_vec = None
        if image_path and image_path.exists():
            try:
                img = Image.open(image_path).convert("RGB")
                inputs = processor(images=img, return_tensors="pt").to(DEVICE)
                with torch.no_grad():
                    image_vec = model.get_image_features(**inputs)
                    image_vec /= image_vec.norm(dim=-1, keepdim=True)
                image_vec = image_vec.cpu().numpy()[0].tolist()
            except Exception as e:
                print(f"Error encoding image {pid}: {e}")

        # Get Text Embedding
        text_vec = None
        text_content = p.get("productDisplayName", "")
        if text_content:
            try:
                inputs = processor(text=[text_content], padding="max_length", return_tensors="pt").to(DEVICE)
                with torch.no_grad():
                    text_vec = model.get_text_features(**inputs)
                    text_vec /= text_vec.norm(dim=-1, keepdim=True)
                text_vec = text_vec.cpu().numpy()[0].tolist()
            except Exception as e:
                print(f"Error encoding text {pid}: {e}")

        # Opting for Image Vector as primary for the collection if available, else text
        vector = image_vec if image_vec else text_vec
        
        if vector:
            collection.upsert(
                ids=[pid],
                embeddings=[vector],
                metadatas=[{"name": p["productDisplayName"], "category": p.get("masterCategory", "")}]
            )

    print("Re-Indexing Complete.")

if __name__ == "__main__":
    reindex()
