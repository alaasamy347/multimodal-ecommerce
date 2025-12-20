"use client";

import { useEffect, useState } from "react";
import { X, Maximize2, AlertCircle } from "lucide-react";

interface ARViewerProps {
  productId: string;
  productName: string;
  onClose: () => void;
}

function ModelViewerComponent({ arInfo }: { arInfo: any }) {
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [modelError, setModelError] = useState(false);

  useEffect(() => {
    // Load model-viewer script dynamically
    const script = document.createElement("script");
    script.type = "module";
    script.src = "https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js";
    
    script.onload = () => {
      console.log("✅ model-viewer script loaded");
      setScriptLoaded(true);
    };

    script.onerror = () => {
      console.error("❌ Failed to load model-viewer script");
      setModelError(true);
    };

    document.head.appendChild(script);

    return () => {
      try {
        document.head.removeChild(script);
      } catch (e) {
        // Script already removed
      }
    };
  }, []);

  useEffect(() => {
    if (scriptLoaded) {
      // Add event listener for model load
      const modelViewer = document.querySelector('model-viewer');
      if (modelViewer) {
        modelViewer.addEventListener('load', () => {
          console.log("✅ 3D model loaded successfully");
          setModelLoaded(true);
        });

        modelViewer.addEventListener('error', (e: any) => {
          console.error("❌ Model load error:", e);
          setModelError(true);
        });
      }
    }
  }, [scriptLoaded]);

  if (!scriptLoaded) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-gray-900 to-black">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading AR Viewer...</p>
          <p className="text-gray-400 text-sm mt-2">Initializing 3D engine...</p>
        </div>
      </div>
    );
  }

  if (modelError) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-gray-900 to-black">
        <div className="text-center text-white px-6">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
          <p className="text-lg mb-2">Failed to load 3D model</p>
          <p className="text-sm text-gray-400 mb-4">Model URL: {arInfo.model_url}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Loading overlay */}
      {!modelLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-gray-900 to-black z-10">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg">Loading 3D Model...</p>
            <p className="text-gray-400 text-sm mt-2">Size: {arInfo.model_size_kb}KB</p>
          </div>
        </div>
      )}

      {/* Model Viewer */}
      <div 
        style={{ width: "100%", height: "100%" }}
        dangerouslySetInnerHTML={{
          __html: `
            <model-viewer
              src="${arInfo.model_url}"
              poster="${arInfo.poster_url}"
              alt="${arInfo.name}"
              ar
              ar-modes="webxr scene-viewer quick-look"
              camera-controls
              touch-action="pan-y"
              auto-rotate
              auto-rotate-delay="3000"
              rotation-per-second="15deg"
              shadow-intensity="1"
              shadow-softness="0.5"
              exposure="1.5"
              camera-orbit="0deg 90deg 105%"
              min-camera-orbit="auto auto 50%"
              max-camera-orbit="auto auto 200%"
              field-of-view="45deg"
              loading="eager"
              reveal="auto"
              environment-image="neutral"
              interaction-prompt="auto"
              style="
                width: 100%; 
                height: 100%; 
                background: linear-gradient(to bottom, #ffffff, #f0f0f0);
                --poster-color: transparent;
              "
            >
              <!-- AR Button -->
              <button 
                slot="ar-button"
                style="
                  position: absolute;
                  bottom: 32px;
                  left: 50%;
                  transform: translateX(-50%);
                  padding: 16px 32px;
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white;
                  font-weight: bold;
                  border-radius: 9999px;
                  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
                  border: none;
                  cursor: pointer;
                  font-size: 16px;
                  display: flex;
                  align-items: center;
                  gap: 8px;
                  transition: all 0.3s ease;
                "
                onmouseover="this.style.transform='translateX(-50%) scale(1.05)'"
                onmouseout="this.style.transform='translateX(-50%) scale(1)'"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                  <line x1="12" y1="22.08" x2="12" y2="12"></line>
                </svg>
                View in Your Space
              </button>
              
              <!-- Progress Bar -->
              <div slot="progress-bar" style="
                height: 3px;
                background: rgba(255, 255, 255, 0.3);
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                overflow: hidden;
              ">
                <div style="
                  height: 100%;
                  background: linear-gradient(90deg, #667eea, #764ba2);
                  width: 0%;
                  transition: width 0.3s;
                "></div>
              </div>
            </model-viewer>
          `
        }}
      />
    </>
  );
}

export function ARViewer({ productId, productName, onClose }: ARViewerProps) {
  const [arInfo, setArInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    console.log("🔍 Fetching AR info for product:", productId);
    
    // Fetch AR info
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/products/${productId}/ar-info`)
      .then(res => {
        console.log("📡 AR info response status:", res.status);
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch AR info`);
        return res.json();
      })
      .then(data => {
        console.log("✅ AR Info received:", data);
        
        if (!data.ar_available) {
          console.warn("⚠️ AR not available:", data.error);
          setError(data.error || "AR not available for this product");
          setLoading(false);
          return;
        }
        
        // Test if model URL is accessible
        fetch(data.model_url, { method: 'HEAD' })
          .then(modelRes => {
            console.log(`📦 Model file check: ${modelRes.status} (${data.model_size_kb}KB)`);
            if (!modelRes.ok) {
              throw new Error("Model file not accessible");
            }
            setArInfo(data);
            setLoading(false);
          })
          .catch(err => {
            console.error("❌ Model file error:", err);
            setError(`Model file not found: ${data.model_url}`);
            setLoading(false);
          });
      })
      .catch(err => {
        console.error("❌ Failed to load AR info:", err);
        setError(`Failed to load AR information: ${err.message}`);
        setLoading(false);
      });
  }, [productId]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-white text-xl mb-2">Loading AR Experience...</div>
          <div className="text-gray-400 text-sm">Product ID: {productId}</div>
        </div>
      </div>
    );
  }

  if (error || !arInfo || !arInfo.ar_available) {
    return (
      <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl max-w-md w-full shadow-2xl">
          <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h3 className="text-2xl font-bold mb-3 text-gray-900 text-center">AR Not Available</h3>
          <p className="text-gray-600 mb-2 text-center">
            {error || "3D model not found for this product"}
          </p>
          {arInfo && (
            <div className="bg-gray-100 p-3 rounded-lg text-xs text-gray-600 mb-4">
              <div>Product: {arInfo.name}</div>
              <div>ID: {productId}</div>
              {arInfo.model_url && <div className="truncate">Model: {arInfo.model_url}</div>}
            </div>
          )}
          <button 
            onClick={onClose} 
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black z-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/90 via-black/50 to-transparent p-6 z-20">
        <div className="flex justify-between items-center">
          <div className="text-white">
            <h2 className="text-2xl font-bold drop-shadow-lg">{arInfo.name}</h2>
            <div className="flex items-center gap-3 mt-2 text-sm">
              <span className="px-2 py-1 bg-white/20 backdrop-blur-sm rounded text-gray-200">
                {arInfo.category}
              </span>
              {arInfo.color && (
                <span className="px-2 py-1 bg-white/20 backdrop-blur-sm rounded text-gray-200">
                  {arInfo.color}
                </span>
              )}
              <span className="text-gray-300 text-xs">
                {arInfo.model_size_kb}KB
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-3 bg-white/20 hover:bg-white/30 rounded-full backdrop-blur-sm transition-all hover:scale-110"
            aria-label="Close AR viewer"
          >
            <X className="w-6 h-6 text-white" />
          </button>
        </div>
      </div>

      {/* Model Viewer */}
      <ModelViewerComponent arInfo={arInfo} />

      {/* Instructions Overlay */}
      <div className="absolute bottom-32 left-0 right-0 text-center pointer-events-none z-10">
        <div className="inline-block bg-black/80 text-white px-6 py-3 rounded-full backdrop-blur-md text-sm border border-white/30 shadow-2xl">
          <div className="hidden sm:block">
            <span className="inline-flex items-center gap-2">
              <span>👆 Drag to rotate</span>
              <span className="text-gray-400">•</span>
              <span>🔍 Pinch to zoom</span>
              <span className="text-gray-400">•</span>
              <span>📱 Tap button for AR</span>
            </span>
          </div>
          <div className="sm:hidden">
            👆 Drag • 🔍 Pinch • 📱 AR
          </div>
        </div>
      </div>

      {/* Debug Info (remove in production) */}
      <div className="absolute bottom-4 right-4 text-xs text-white/50 pointer-events-none">
        Model: {arInfo.model_size_kb}KB
      </div>
    </div>
  );
}