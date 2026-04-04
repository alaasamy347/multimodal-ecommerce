"use client";

import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

interface ImageGeneratorProps {
  onGenerateComplete: (imageUrl: string, prompt: string) => void;
  onCancel: () => void;
}

export function ImageGenerator({ onGenerateComplete, onCancel }: ImageGeneratorProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const form = new FormData();
      form.append("prompt", prompt);
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/generate_image`, {
        method: "POST",
        body: form,
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || `Backend error ${res.status}`);
      }
      
      const data = await res.json();
      onGenerateComplete(data.image_url, prompt);
    } catch (err: any) {
      setError(err.message || "Failed to generate image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl relative overflow-hidden">
        <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
          ✨ AI Image Generator
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          Describe the perfect piece of furniture, and we'll generate it for you to search our catalog!
        </p>
        
        <div className="space-y-4">
          <div>
            <Input
              autoFocus
              placeholder="e.g. A futuristic glass desk with neon edges..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleGenerate();
              }}
              disabled={loading}
              className="w-full"
            />
          </div>
          
          {error && (
            <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">
              ❌ {error}
            </div>
          )}
          
          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={onCancel} disabled={loading} className="flex-1">
              Cancel
            </Button>
            <Button onClick={handleGenerate} disabled={loading || !prompt.trim()} className="flex-1 bg-violet-600 hover:bg-violet-700 font-medium">
              {loading ? "Generating..." : "Generate & Search"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
