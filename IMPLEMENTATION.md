# Unified Multimodal Architecture for Enhanced E-Commerce

This document outlines the current architecture, implementation steps, and design rationale for the Multimodal E-Commerce Discovery platform.

## 🏗️ Project Structure

### Backend (FastAPI + PyTorch)
- `main.py`: Central orchestrator handling FAISS indexing, search logic, VLM integration, and voice processing.
- `server.py`: Clean Architecture wrapper for services.
- `data/`: Contains product catalogs (`clean_products.json`) and FAISS indices.
- `use_cases/`: Business logic for search and checkout services.

### Frontend (Next.js 15 + Tailwind CSS)
- `src/app/`: Next.js 15 App Router pages (Home, Checkout, Confirmation).
- `src/components/`: Modular React components.
  - `SearchInterface.tsx`: Main search dashboard and chat logic.
  - `UnifiedSearchInput.tsx`: Multimodal input field (Text, Image, Voice).
  - `ImageGenerator.tsx`: Generative AI prototyping tool.
  - `CartDrawer.tsx`: Sidebar for cart management.
- `src/hooks/`: Custom React hooks (e.g., `useCart`, `useTypewriter`).

---

## 🚀 Implementation Steps Followed

### 1. Unified Search Foundation
- **Step**: Implemented hybrid retrieval using **CLIP (ViT-B/32)**.
- **Why**: CLIP allows mapping both text and images into the same vector space, enabling visual-semantic search.
- **Pros**: Handles "zero-shot" queries (e.g., "vintage style") without specific metadata.
- **Cons**: Can be slow on CPUs; requires efficient indexing (FAISS).

### 2. Multi-Image & Multimodal Input
- **Step**: Refactored `UnifiedSearchInput` to support multiple simultaneous image uploads and voice recording.
- **Why**: Real-world users often have multiple inspiration photos or want to describe what they see while showing a photo.

### 3. VLM Reasoning (Vision-Language Model)
- **Step**: Integrated **Ollama with LLaVA** for complex reasoning.
- **Why**: Standard embeddings can't answer "What color is this sofa?" or "Is this suitable for a small apartment?". LLaVA provides structured metadata extraction from images.
- **Pros**: Deep semantic understanding.
- **Cons**: High latency (~2-5 seconds per query). Optimized by running VLM in the background or only for specific queries.

### 4. Generative Prototyping
- **Step**: Integrated **Pollinations.ai** for furniture image generation.
- **Why**: If a user can't find a product, they can "create" it. This aligns with the academic proposal for "Unified Multimodal Architecture".

### 5. Robust Color Filtering
- **Step**: Implemented a "Soft Filter" logic in `main.py`.
- **Why**: Metadata is often incomplete. Strict filtering (rejecting if color isn't in JSON) led to empty results. The current logic prioritizes matches but allows visual matches to persist.

---

## 🛠️ Technology Stack & Rationale

| Feature | Tool / Model | Rationale | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **Embeddings** | CLIP (OpenAI) | Standard for Multimodal | Fast retrieval, great accuracy | Large model size |
| **Vector DB** | FAISS | Efficient CPU search | Extremely fast (~ms) | No native metadata filter |
| **VLM** | LLaVA (via Ollama) | Local, Private, Robust | Structured JSON output | Computationally heavy |
| **Voice** | OpenAI Whisper | Industry leader in ASR | High accuracy with noise | Requires GPU for real-time |
| **Frontend** | Next.js 15 | Modern, Server Actions | Fast loading, SEO ready | Steep learning curve |

---

## 🔧 Current State & Fixes Applied
- **Search Issue**: Fixed overly aggressive color filtering that caused 0 results for "blue sofa".
- **Checkout Issue**: Resolved redundant backend calls and fixed missing `/checkout/cart/add` endpoint.
- **UI Polishing**: Synchronized AI feedback summary to provide actionable tips when results are low.
