"""
Quick Fix: Update the keep_warm parameter and improve image detection
Replace your modal_app.py with this version
"""
import modal
import os

app = modal.App("furniture-search-api")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi==0.104.1",
        "python-multipart==0.0.6",
        "Pillow==10.1.0",
        "numpy==1.24.3",
        "torch==2.1.0",
        "transformers==4.35.2",
        "faiss-cpu==1.7.4",
        "kaggle==1.5.16",
    )
)

volume = modal.Volume.from_name("furniture-data-cache", create_if_missing=True)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("kaggle-secrets")],
    volumes={"/cache": volume},
    memory=2048,
    timeout=600,  # 10 minutes timeout
    min_containers=0,  # Keep at least 1 container always running
    max_containers=3,  # Scale up to 10 if needed
    container_idle_timeout=60,  # Keep idle containers for 5 minutes
    allow_concurrent_inputs=100,  # Handle up to 100 concurrent requests
)
@modal.asgi_app()
def serve():
    import os
    import json
    import tempfile
    from typing import Optional
    import numpy as np
    import torch
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from PIL import Image as PILImage
    from transformers import CLIPProcessor, CLIPModel
    import faiss
    
    api = FastAPI(title="Furniture Search API")
    
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global state
    _clip_model = None
    _clip_processor = None
    _data_loaded = False
    _products = None
    _image_index = None
    _text_index = None
    _id_map = None
    _images_dir = None  # Will be set dynamically
    
    KAGGLE_DATASET = "alaasamy1/amazon-data2"
    CACHE_DIR = "/cache/data"
    
    def find_images_directory():
        """Recursively search for images directory"""
        print("🔍 Searching for images directory...")
        
        # Possible locations (including nested paths from zip extraction)
        possible_paths = [
            "/cache/images",
            "/cache/data/images",
            "/cache/data/images/images",  # ← Nested from zip
            os.path.join(CACHE_DIR, "images"),
            os.path.join(CACHE_DIR, "images", "images"),  # ← Nested from zip
        ]
        
        # Check known paths first
        for path in possible_paths:
            if os.path.exists(path):
                # Verify it has subdirectories with images
                try:
                    subdirs = [d for d in os.listdir(path) 
                              if os.path.isdir(os.path.join(path, d))]
                    # Check if subdirs contain actual image files
                    has_images = False
                    for subdir in subdirs[:3]:  # Check first 3 subdirs
                        subdir_path = os.path.join(path, subdir)
                        files = os.listdir(subdir_path)
                        if any(f.endswith(('.jpg', '.jpeg', '.png')) for f in files):
                            has_images = True
                            break
                    
                    if has_images:
                        print(f"✅ Found images at: {path}")
                        print(f"   Categories: {subdirs[:5]}")
                        return path
                except:
                    continue
        
        # Search recursively
        print(f"🔍 Searching recursively in {CACHE_DIR}...")
        for root, dirs, files in os.walk(CACHE_DIR):
            if 'images' in dirs:
                images_path = os.path.join(root, 'images')
                # Verify it has subdirectories with images
                try:
                    subdirs = [d for d in os.listdir(images_path) 
                              if os.path.isdir(os.path.join(images_path, d))]
                    if subdirs:
                        # Check if subdirs actually contain images
                        for subdir in subdirs[:3]:
                            subdir_path = os.path.join(images_path, subdir)
                            files = os.listdir(subdir_path)
                            if any(f.endswith(('.jpg', '.jpeg', '.png')) for f in files):
                                print(f"✅ Found images directory: {images_path}")
                                print(f"   Categories: {subdirs[:5]}")
                                return images_path
                except:
                    continue
        
        print("❌ No images directory found!")
        return None
    
    def download_entire_dataset():
        """Download complete dataset from Kaggle"""
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            kaggle_api = KaggleApi()
            kaggle_api.authenticate()
            
            print(f"📥 Downloading entire dataset from Kaggle...")
            kaggle_api.dataset_download_files(
                dataset=KAGGLE_DATASET,
                path=CACHE_DIR,
                unzip=True
            )
            
            print(f"✅ Dataset downloaded!")
            
            # Show what was downloaded
            print("\n📂 Downloaded contents:")
            items = os.listdir(CACHE_DIR)
            for item in items[:20]:
                item_path = os.path.join(CACHE_DIR, item)
                if os.path.isdir(item_path):
                    print(f"   📁 {item}/")
                else:
                    size_mb = os.path.getsize(item_path) / (1024 * 1024)
                    print(f"   📄 {item} ({size_mb:.2f} MB)")
            
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_data():
        nonlocal _data_loaded, _products, _image_index, _text_index, _id_map, _images_dir
        
        if _data_loaded:
            return True
        
        print("\n" + "="*60)
        print("🚀 Initializing data...")
        print("="*60)
        
        try:
            # Download dataset if not exists
            products_path = os.path.join(CACHE_DIR, "clean_products.json")
            if not os.path.exists(products_path):
                print("📦 Dataset not cached, downloading...")
                if not download_entire_dataset():
                    return False
            
            # Find images directory
            _images_dir = find_images_directory()
            
            if _images_dir is None:
                print("\n⚠️ WARNING: Images not found!")
                print("   The API will work but won't serve images.")
                print("   Please ensure your Kaggle dataset includes 'images/' folder")
            
            # Load products
            print(f"\n📦 Loading products from: {products_path}")
            with open(products_path, "r", encoding="utf-8") as f:
                products_list = json.load(f)
                _products = {int(p["id"]): p for p in products_list}
            print(f"✅ Loaded {len(_products)} products")
            
            # Load FAISS indexes
            print("\n📊 Loading FAISS indexes...")
            _image_index = faiss.read_index(os.path.join(CACHE_DIR, "image_index.faiss"))
            _text_index = faiss.read_index(os.path.join(CACHE_DIR, "text_index.faiss"))
            _id_map = np.load(os.path.join(CACHE_DIR, "id_map.npy"))
            
            print(f"✅ Image index: {_image_index.ntotal} vectors")
            print(f"✅ Text index: {_text_index.ntotal} vectors")
            print(f"✅ ID map: {len(_id_map)} IDs")
            
            _data_loaded = True
            print("\n✅ Initialization complete!")
            return True
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_clip():
        nonlocal _clip_model, _clip_processor
        
        if _clip_model is not None:
            return True
        
        try:
            print("\n🔧 Loading CLIP model...")
            device = torch.device("cpu")
            _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
            _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            _clip_model.eval()
            print("✅ CLIP loaded")
            return True
        except Exception as e:
            print(f"❌ CLIP failed: {e}")
            return False
    
    def search_with_embedding(embedding, index, top_k=20):
        distances, indices = index.search(embedding, top_k * 3)
        results = []
        
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            
            product_id = int(_id_map[int(idx)])
            product = _products.get(product_id)
            if not product:
                continue
            
            score = float((dist + 1.0) / 2.0)
            
            results.append({
                "id": product_id,
                "name": product.get("productDisplayName", ""),
                "category": product.get("masterCategory", ""),
                "subCategory": product.get("subCategory", ""),
                "image": product.get("image_path", ""),
                "color": product.get("color", product.get("baseColour", "")),
                "score": score,
                "has_3d_model": product.get("has_3d_model", False)
            })
            
            if len(results) >= top_k * 2:
                break
        
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
    
    # ========================================
    # ENDPOINTS
    # ========================================
    
    @api.get("/")
    def root():
        """Root endpoint with system status"""
        try:
            return {
                "message": "Furniture Search API",
                "status": "online",
                "version": "1.0.0",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "system": {
                    "data_loaded": _data_loaded,
                    "clip_loaded": _clip_model is not None,
                    "images_available": _images_dir is not None,
                    "images_path": _images_dir,
                    "products_count": len(_products) if _products else 0
                },
                "endpoints": {
                    "search": "/search/intelligent (POST)",
                    "health": "/health (GET)",
                    "test": "/test-image (GET)",
                    "images": "/static/{image_path} (GET)"
                }
            }
        except Exception as e:
            return {
                "message": "API running but not fully initialized",
                "status": "starting",
                "error": str(e)
            }
    
    @api.get("/health")
    def health():
        """Health check for monitoring"""
        return {
            "status": "healthy" if _data_loaded else "initializing",
            "data_initialized": _data_loaded,
            "model_initialized": _clip_model is not None,
            "images_ready": _images_dir is not None,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    
    @api.get("/wake-up")
    def wake_up():
        """Endpoint to wake up and initialize the service"""
        if not _data_loaded:
            print("🔄 Wake-up call received, initializing...")
            initialize_data()
        if _clip_model is None:
            initialize_clip()
        
        return {
            "message": "Service is awake and ready",
            "data_loaded": _data_loaded,
            "clip_loaded": _clip_model is not None,
            "images_ready": _images_dir is not None
        }
    
    @api.get("/test-image")
    def test_image():
        if not _data_loaded:
            initialize_data()
        
        response = {
            "images_dir": _images_dir,
            "images_found": _images_dir is not None,
            "cache_structure": {},
            "sample_product": None
        }
        
        # Show cache structure
        if os.path.exists(CACHE_DIR):
            items = os.listdir(CACHE_DIR)
            response["cache_structure"] = {
                "path": CACHE_DIR,
                "contents": items[:20],
                "subdirs": [d for d in items if os.path.isdir(os.path.join(CACHE_DIR, d))]
            }
        
        # Show images structure
        if _images_dir and os.path.exists(_images_dir):
            subdirs = [d for d in os.listdir(_images_dir) 
                      if os.path.isdir(os.path.join(_images_dir, d))]
            response["images_structure"] = {
                "path": _images_dir,
                "categories": subdirs,
                "sample_images": []
            }
            
            # Get sample images
            if subdirs:
                first_cat = subdirs[0]
                cat_path = os.path.join(_images_dir, first_cat)
                samples = os.listdir(cat_path)[:3]
                response["images_structure"]["sample_images"] = [
                    f"{first_cat}/{img}" for img in samples
                ]
        
        # Show sample product
        if _products:
            first = list(_products.values())[0]
            image_path = first.get("image_path", "")
            full_path = os.path.join(_images_dir, image_path) if _images_dir else None
            
            response["sample_product"] = {
                "id": first.get("id"),
                "name": first.get("productDisplayName"),
                "image_path": image_path,
                "full_image_path": full_path,
                "image_exists": os.path.exists(full_path) if full_path else False
            }
        
        return response
    
    @api.get("/static/{image_path:path}")
    async def serve_image(image_path: str):
        if not _data_loaded:
            initialize_data()
        
        if _images_dir is None:
            raise HTTPException(
                status_code=503, 
                detail="Images not available. Please upload images/ folder to Kaggle dataset."
            )
        
        full_path = os.path.join(_images_dir, image_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Image not found: {image_path}"
            )
        
        return FileResponse(
            full_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )
    
    @api.post("/search/intelligent")
    async def intelligent_search(
        query: str = Form(""),
        image: UploadFile = File(None),
        top_k: int = Form(10)
    ):
        try:
            if not _data_loaded:
                if not initialize_data():
                    return JSONResponse(
                        status_code=500,
                        content={"error": "Failed to initialize"}
                    )
            
            if _clip_model is None:
                if not initialize_clip():
                    return JSONResponse(
                        status_code=500,
                        content={"error": "Failed to load CLIP"}
                    )
            
            modality_embeddings = []
            device = torch.device("cpu")
            
            # Process IMAGE
            if image:
                tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp_img.write(await image.read())
                tmp_img.close()
                
                try:
                    with torch.no_grad():
                        pil_img = PILImage.open(tmp_img.name).convert("RGB")
                        img_inputs = _clip_processor(images=pil_img, return_tensors="pt").to(device)
                        img_emb = _clip_model.get_image_features(**img_inputs)
                        img_emb = img_emb.cpu().numpy()
                        img_emb /= np.linalg.norm(img_emb, axis=1, keepdims=True)
                    modality_embeddings.append(img_emb[0])
                finally:
                    os.remove(tmp_img.name)
            
            # Process TEXT
            if query.strip():
                with torch.no_grad():
                    txt_inputs = _clip_processor(
                        text=[query], 
                        return_tensors="pt", 
                        padding=True, 
                        truncation=True, 
                        max_length=77
                    ).to(device)
                    txt_emb = _clip_model.get_text_features(**txt_inputs)
                    txt_emb = txt_emb.cpu().numpy()
                    txt_emb /= np.linalg.norm(txt_emb, axis=1, keepdims=True)
                modality_embeddings.append(txt_emb[0])
            
            if not modality_embeddings:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No input provided"}
                )
            
            # Combine and search
            final_embedding = np.mean(modality_embeddings, axis=0, keepdims=True)
            final_embedding /= np.linalg.norm(final_embedding, axis=1, keepdims=True)
            final_embedding = final_embedding.astype("float32")
            
            search_index = _image_index if (image and not query) else _text_index
            results = search_with_embedding(final_embedding, search_index, top_k)
            
            return {
                "query": query,
                "interpreted_query": query,
                "accurate_results": results,
                "related_results": [],
                "total_results": len(results),
                "images_available": _images_dir is not None
            }
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"error": str(e)}
            )
    
    return api