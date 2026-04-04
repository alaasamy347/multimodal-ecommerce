"use client";

import { useEffect, useState, useRef } from "react";
import { X } from "lucide-react";

interface ARViewerProps {
  productId: string;
  onClose: () => void;
}

export function ARViewer({ productId, onClose }: ARViewerProps) {
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        setError("");

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        console.log(`🔍 Fetching product ${productId} from ${apiUrl}`);

        const response = await fetch(`${apiUrl}/products/${productId}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: Failed to fetch product`);
        }

        const foundProduct = await response.json();
        console.log("📦 Product data:", foundProduct);

        if (!foundProduct.model_url) {
          console.error("❌ No model_url in product data");
          throw new Error("3D model not available for this product");
        }

        console.log("✅ Model URL:", foundProduct.model_url);

        // Test if model URL is accessible
        try {
          const modelCheck = await fetch(foundProduct.model_url, { method: 'HEAD' });
          console.log(`🔍 Model URL check: ${modelCheck.status}`);

          if (!modelCheck.ok) {
            throw new Error(`Model file not accessible (HTTP ${modelCheck.status})`);
          }
        } catch (err) {
          console.error("❌ Model URL not accessible:", err);
          throw new Error("3D model file not found on server");
        }

        setProduct(foundProduct);
      } catch (err: any) {
        console.error("❌ Failed to load product:", err);
        setError(err.message || "Failed to load AR experience");
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [productId]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Loading AR Experience
          </h3>
          <p className="text-gray-600">Preparing 3D model...</p>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">⚠️</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              AR Not Available
            </h3>
            <p className="text-gray-600 mb-4">{error || "Failed to load AR experience"}</p>
            {product && product.model_url && (
              <p className="text-xs text-gray-400 break-all">
                Model: {product.model_url}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-4 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="text-white">
            <h2 className="text-xl font-semibold">{product.name}</h2>
            <p className="text-sm text-gray-300">{product.subCategory}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition"
            aria-label="Close"
          >
            <X className="w-6 h-6 text-white" />
          </button>
        </div>
      </div>

      {/* 3D Viewer */}
      <div className="w-full h-full flex items-center justify-center p-4 pt-20 pb-32">
        <div className="w-full h-full max-w-5xl">
          <ModelViewer
            modelUrl={product.model_url}
            posterUrl={product.image_url}
            productName={product.name}
          />
        </div>
      </div>

      {/* Instructions */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 text-white">
            <p className="text-sm text-center mb-2 font-medium">💡 How to use AR</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="flex items-start gap-2">
                <span className="text-purple-400">🖱️</span>
                <span>Click and drag to rotate</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-purple-400">🔍</span>
                <span>Scroll to zoom in/out</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-purple-400">📱</span>
                <span>Tap "View in AR" to see in your space</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ModelViewerProps {
  modelUrl: string;
  posterUrl?: string;
  productName: string;
}

function ModelViewer({ modelUrl, posterUrl, productName }: ModelViewerProps) {
  const [modelError, setModelError] = useState(false);
  const [modelLoading, setModelLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    console.log("🔧 ModelViewer mounting...");
    console.log("   Model URL:", modelUrl);
    console.log("   Poster URL:", posterUrl);

    // Load model-viewer script
    const script = document.createElement("script");
    script.type = "module";
    script.src = "https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js";

    script.onload = () => {
      console.log("✅ model-viewer library loaded");

      // Give it a moment to initialize
      setTimeout(() => {
        if (containerRef.current) {
          const modelViewer = containerRef.current.querySelector('model-viewer');
          if (modelViewer) {
            console.log("✅ model-viewer element found");

            // Add event listeners
            modelViewer.addEventListener('load', () => {
              console.log("✅ 3D model loaded successfully");
              setModelLoading(false);
            });

            modelViewer.addEventListener('error', (event: any) => {
              console.error("❌ Model loading error:", event);
              setModelError(true);
              setModelLoading(false);
            });

            // Timeout fallback - hide loading after 10 seconds regardless
            setTimeout(() => {
              console.log("⏱️ Timeout reached, hiding loading screen");
              setModelLoading(false);
            }, 10000);
          } else {
            console.error("❌ model-viewer element not found in DOM");
          }
        }
      }, 500);
    };

    script.onerror = () => {
      console.error("❌ Failed to load model-viewer library");
      setModelError(true);
      setModelLoading(false);
    };

    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, [modelUrl]);

  if (modelError) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-900 rounded-xl">
        <div className="text-center text-white p-8">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold mb-2">Failed to Load 3D Model</h3>
          <p className="text-gray-400 mb-4">The 3D model file could not be loaded.</p>
          <div className="text-left bg-gray-800 rounded p-3 text-xs">
            <p className="text-gray-500 mb-1">Model URL:</p>
            <p className="text-red-400 break-all font-mono">{modelUrl}</p>
          </div>
          <p className="text-gray-500 text-xs mt-4">
            Check browser console for more details
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative" ref={containerRef}>
      {modelLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 rounded-xl z-20">
          <div className="text-center text-white">
            <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-lg font-medium mb-2">Loading 3D Model...</p>
            <p className="text-sm text-gray-400">This may take a few seconds</p>
          </div>
        </div>
      )}

      {/* Use dangerouslySetInnerHTML but add onLoad handlers via useEffect */}
      <div
        className="w-full h-full"
        dangerouslySetInnerHTML={{
          __html: `
            <model-viewer
              src="${modelUrl}"
              ${posterUrl ? `poster="${posterUrl}"` : ''}
              alt="${productName}"
              ar
              ar-modes="webxr scene-viewer quick-look"
              camera-controls
              auto-rotate
              shadow-intensity="1"
              environment-image="neutral"
              exposure="1.2"
              tone-mapping="commerce"
              style="width: 100%; height: 100%; border-radius: 1rem; background-color: #1f2937; --poster-color: transparent;"
            >
              <button
                slot="ar-button"
                style="
                  position: absolute;
                  bottom: 20px;
                  left: 50%;
                  transform: translateX(-50%);
                  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
                  color: white;
                  padding: 14px 28px;
                  border-radius: 12px;
                  border: none;
                  font-size: 16px;
                  font-weight: 600;
                  cursor: pointer;
                  display: flex;
                  align-items: center;
                  gap: 10px;
                  box-shadow: 0 8px 16px rgba(124, 58, 237, 0.4);
                  transition: all 0.3s ease;
                "
                onmouseover="this.style.transform='translateX(-50%) scale(1.05)'"
                onmouseout="this.style.transform='translateX(-50%) scale(1)'"
              >
                <span style="font-size: 20px;">📱</span>
                <span>View in Your Space</span>
              </button>
              
              <div slot="progress-bar" style="display: none;"></div>
            </model-viewer>
          `
        }}
      />
    </div>
  );
}