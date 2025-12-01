"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, Search } from "lucide-react";
import { SearchCard } from "./SearchCard";
import { UnifiedSearchInput } from "./UnifiedSearchInput";

export default function SearchInterface() {
  const [accurateResults, setAccurateResults] = useState<any[]>([]);
  const [relatedResults, setRelatedResults] = useState<any[]>([]);
  const [aiSummary, setAiSummary] = useState<string>("");
  const [detectedColor, setDetectedColor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchInfo, setSearchInfo] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function handleSearch(data: { query: string; image: File | null; audio: File | null }) {
    let res: Response;
    setLoading(true);
    setError("");
    setAccurateResults([]);
    setRelatedResults([]);
    setAiSummary("");
    setSearchInfo("");

    try {
      const form = new FormData();
      form.append("top_k", "10");
      form.append("session_id", "default");

      // if (data.image) form.append("file", data.image);
      if (data.query) form.append("query", data.query);

      // Only append files if they exist
      if (data.image) form.append("image", data.image);
      if (data.audio) form.append("audio", data.audio);

      res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/search/intelligent`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const responseData = await res.json();
      console.log("🔍 Response:", responseData);

      setAccurateResults(responseData.accurate_results || []);
      setRelatedResults(responseData.related_results || []);
      setAiSummary(responseData.ai_summary || "");
      setSearchInfo(
        `🧠 AI Multimodal Search: "${responseData.interpreted_query || data.query}"`
      );

      if (
        (!responseData.accurate_results || responseData.accurate_results.length === 0) &&
        (!responseData.related_results || responseData.related_results.length === 0)
      ) {
        setError("No results found. Try different keywords or images.");
      }
    } catch (err) {
      console.error("Search error:", err);
      setError("Search failed. Please ensure backend (port 8000) is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium mb-4 shadow-lg">
            <Sparkles className="w-4 h-4" />
            AI-Powered Search
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-4 tracking-tight">
            Multimodal Search
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Search using images, text, or voice. Our AI understands what you're looking for.
          </p>
        </div>

        {/* Search Input */}
        <div className="mb-12">
          <UnifiedSearchInput onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="bg-red-50 border-red-200">
              <CardContent className="p-4 text-red-700">⚠️ {error}</CardContent>
            </Card>
          </div>
        )}

        {/* AI Summary */}
        {aiSummary && (
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="bg-green-50 border-green-200 shadow-sm">
              <CardContent className="p-4 text-green-900 font-medium">
                🧠 {aiSummary}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Search Info */}
        {searchInfo && (
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 shadow-sm">
              <CardContent className="p-4 text-blue-900 font-medium">
                {searchInfo}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Color Detection */}
        {detectedColor && (
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-purple-700">
                  <Sparkles className="w-4 h-4" />
                  <span className="font-medium">
                    Detected Color:{" "}
                    <span className="capitalize">{detectedColor}</span>
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Accurate Results */}
        {accurateResults.length > 0 && (
          <div className="max-w-7xl mx-auto mb-12">
            <div className="mb-6 text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Best Matches</h2>
              <p className="text-gray-600">
                Found {accurateResults.length} high-confidence results
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
              {accurateResults.map((product, idx) => (
                <SearchCard key={`${product.id}-${idx}`} {...product} />
              ))}
            </div>
          </div>
        )}

        {/* Related Results */}
        {relatedResults.length > 0 && (
          <div className="max-w-7xl mx-auto">
            <div className="mb-6 text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                You Might Also Like
              </h2>
              <p className="text-gray-600">
                Showing {relatedResults.length} related or alternative items
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
              {relatedResults.map((product, idx) => (
                <SearchCard key={`${product.id}-${idx}`} {...product} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading &&
          accurateResults.length === 0 &&
          relatedResults.length === 0 &&
          !error && (
            <div className="max-w-2xl mx-auto text-center py-16">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
                <Search className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                Ready to Search
              </h3>
              <p className="text-gray-600 mb-6">
                Upload an image, enter text like "blue chair" or "wooden table",
                or use voice search to find products.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-xl mx-auto">
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <div className="text-2xl mb-2">📝</div>
                  <div className="font-semibold text-sm mb-1">Text Search</div>
                  <div className="text-xs text-gray-600">
                    Type: "yellow pants", "black shoes"
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <div className="text-2xl mb-2">🖼️</div>
                  <div className="font-semibold text-sm mb-1">Image Search</div>
                  <div className="text-xs text-gray-600">
                    Upload a product photo
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-gray-200">
                  <div className="text-2xl mb-2">🎤</div>
                  <div className="font-semibold text-sm mb-1">Voice Search</div>
                  <div className="text-xs text-gray-600">
                    Say what you're looking for
                  </div>
                </div>
              </div>
            </div>
          )}
      </div>
    </div>
  );
}
