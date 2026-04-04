# Multimodal E-Commerce Product Discovery: Architecture & Implementation

This document serves as the master technical context and implementation diary for the multimodal e-commerce project. It explains the project's structure, the precise steps taken to achieve the current state, and the rationale behind every AI/ML model choice (including pros and cons).

## 📌 Project Overview
The architecture enables users to search an e-commerce catalog through seamlessly combined **text, voice, and multiple images**. It additionally implements two major enhancements: Complex Visual Reasoning to understand ambiguous intents, and a Generative Design Sandbox to prototype missing concepts.

---

## 🛠️ Implementation Steps Followed

The system was built following a structured 4-phase "missing enhancements" pipeline to fulfill an advanced research proposal:

1. **Foundational API Adjustments**:
   - Refactored the core `_do_search` function and `/search/intelligent` POST endpoint within `backend/main.py`.
   - Switched inputs from a single `UploadFile` to an array (`List[UploadFile]`) and refactored the frontend `UnifiedSearchInput.tsx` to handle an array of `File` selections natively using `FileReader`.
   - **Result**: The core data pipeline was successfully prepped for multimodality.

2. **Multiple Image Queries (MIQ)**:
   - Evaluated the CLIP model to run sequentially across multiple images instead of just one.
   - For each uploaded image, CLIP extracts a tensor embedding.
   - Aggregated these embeddings alongside the transcription/text embeddings using an **Arithmetic Mean Vector**. Normalization is done recursively.
   - **Result**: Users can now upload an image of a red sofa and a wooden desk, and the Faiss vector search retrieves hybrid items that combine qualities of both.

3. **Complex Visual Reasoning (VLM Integration)**:
   - Complex queries (e.g., uploading 2 images and saying "Find me a chair style matching this room but in the color of that rug") are difficult for standard vector arithmetic to understand conceptually.
   - Integrated a local Vision-Language Model (`llava` via Ollama) into `backend/main.py` (`_process_with_vlm`).
   - Defined strict system logic: We push the base64-encoded images and transcript to `llava`, enforcing a pure JSON reply.
   - **Result**: The VLM intercepts complex logic, outputs a strict property filter (e.g., `{"color": "brown"}`), which cascades back down into the standard Faiss filter.

4. **Image Generation (Generative Sandbox)**:
   - Added a new React component `ImageGenerator.tsx`, presenting users with a text-to-image interface.
   - Integrated an external API endpoint pointing to `pollinations.ai` inside `backend/main.py` (`/generate_image`).
   - Engineered the frontend to immediately convert the generated image into a visual search payload dynamically dropping it onto the search bar.
   - **Result**: If a user cannot find a reference image, they generate it inside our web app, then seamlessly apply it against the vector store.

---

## 🧠 Model Choices, Rationale, and Trade-Offs

Why did we pick these specific models over alternatives? Below is a breakdown of the models powering the stack:

### 1. Vector Extraction: OPENAI CLIP (`openai/clip-vit-base-patch32`)
**Role**: Extracts 512-dimensional floating vectors from both texts and images simultaneously into the same shared semantic space.
- **Why we chose it**: Legacy systems rely on traditional CNNs (like ResNet50) for images and BERT for text, creating two separate disjointed vector spaces. CLIP learns the relationship between images and text universally, meaning "Red Sofa" text directly overlays on top of a red sofa photograph in mathematical space automatically.
- **PROS**: Unifies text and image data automatically; heavily open-sourced (HuggingFace); very small RAM footprint (loads in ~30s on CPU).
- **CONS**: `vit-base-patch32` is not very detail-oriented and cannot easily distinguish tiny complex patterns or text written inside images. 

### 2. Retrieval Engine: FAISS (`faiss-cpu`)
**Role**: Performs K-Nearest-Neighbors (k-NN) queries to find products fast.
- **Why we chose it**: Alternatives like Pinecone or Weaviate are cloud-based and cost money or latency. 
- **PROS**: Extremely fast, purely local, and requires zero Docker setup/databases. 
- **CONS**: Has to be strictly loaded entirely into RAM (memory limitation for massive datasets of 10M+ rows). 

### 3. Audio Transcription: WHISPER (`openai-whisper tiny`)
**Role**: Processes raw `WAV` microphone byte strings recorded by the frontend.
- **Why we chose it**: Alternatives like Google Cloud Speech-to-Text cost money and require Internet access. 
- **PROS**: 100% free, entirely localized, heavily resilient to accent differences, very small hardware footprint (using the `tiny` model).
- **CONS**: Processing can be slower than commercial API alternatives on low-end CPUs; sometimes hallucinates text in absolute silence.

### 4. Vision Language Model: LLaVA via Ollama (`llava`)
**Role**: Acts as the intelligent "eyes and brain" when complex logical user commands are issued (Phase 3).
- **Why we chose it**: Initially, alternatives like OpenAI's `gpt-4o-mini` API were considered. However, an offline, free solution was requested. Ollama manages quantization natively, allowing a massive visual-LLM to run smoothly inside limited VRAM environments.
- **PROS**: Completely free; private processing; heavily quantized so it runs on basic consumer cards or CPUs decently.
- **CONS**: Susceptible to hallucination; slower to parse 2+ images compared to GPT-4o; struggles with adhering strictly to JSON formatting occasionally.

### 5. Image Generation: Pollinations.ai API Wrapper
**Role**: Powers the Generative Design Sandbox instantly generating furniture (Phase 4).
- **Why we chose it**: We originally attempted to utilize HuggingFace's `diffusers` library using `stabilityai/sd-turbo` locally. However, doing so forced the backend to trigger a massive multi-gigabyte (~7GB) download on startup and severely crashed CPUs without dedicated 16GB GPUs. Moving to the `Pollinations.ai` free endpoint mitigated all of this.
- **PROS**: Zero disk space required; zero local GPU VRAM required; lightning-fast inference (~2 seconds); totally anonymous and free.
- **CONS**: Requires reliable Internet access; prompt manipulation relies entirely on their backend system safety filters.

---

## 🚦 Important Considerations for AI Assistants
If you are an AI tasked with maintaining or updating this codebase, adhere to these constraints:
1. **Lazy Loading Rules**: Always wrap ML model initializations in `threading.Lock()` checks (e.g., `_clip_lock`) if extending or introducing new models into `backend/main.py`. Do not initialize globally.
2. **Backend Environment**: Always respect the `venv` virtual environment in the `backend/` directory when appending packages globally.
3. **Architecture Preservation**: Treat external free API wrappers (like Pollinations) favorably over multi-gigabyte dependency integrations (like `diffusers`/`SDXL`) since we prioritize minimal CPU overhead and instant server responses. Do not revert to local Stable Diffusion without explicit user consent.
