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
    setLoading(true);
    setError("");
    setAccurateResults([]);
    setRelatedResults([]);
    setAiSummary("");
    setSearchInfo("");
    setDetectedColor(null);

    try {
      const form = new FormData();
      form.append("top_k", "20");
      form.append("session_id", "default");
      if (data.query) form.append("query", data.query);
      if (data.image) form.append("file", data.image);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/search/intelligent`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const responseData = await res.json();
      console.log("Search response:", responseData);

      const accurate = (responseData.accurate_results || []).slice(0, 12);
      const related = (responseData.related_results || []).slice(0, 12);

      // dedupe by id and pick highest-scored entry if duplicates
      const dedupe = (arr: any[]) => {
        const map = new Map();
        for (const it of arr) {
          if (!map.has(it.id) || map.get(it.id).score < it.score) {
            map.set(it.id, it);
          }
        }
        return Array.from(map.values()).sort((a,b)=>b.score - a.score);
      };

      const dedupAcc = dedupe(accurate);
      const dedupRel = dedupe(related);

      setAccurateResults(dedupAcc);
      setRelatedResults(dedupRel);
      setAiSummary(responseData.ai_summary || "");
      setSearchInfo(`AI Multimodal: "${responseData.interpreted_query || data.query}"`);

      // If backend provided a detected color, show it
      if (responseData.color_filter) {
        setDetectedColor(responseData.color_filter);
      }

      // show friendly message if no results
      if ((dedupAcc.length === 0) && (dedupRel.length === 0)) {
        setError("No results found. Try different keywords or upload an image.");
      }
    } catch (err) {
      console.error("Search error:", err);
      setError("Search failed. Please ensure backend is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="container mx-auto px-6 py-12">
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

        <div className="mb-8">
          <UnifiedSearchInput onSearch={handleSearch} loading={loading} />
        </div>

        {error && (
          <div className="max-w-4xl mx-auto mb-6">
            <Card className="bg-red-50 border-red-200">
              <CardContent className="p-4 text-red-700">⚠️ {error}</CardContent>
            </Card>
          </div>
        )}

        {aiSummary && (
          <div className="max-w-4xl mx-auto mb-6">
            <Card className="bg-green-50 border-green-200 shadow-sm">
              <CardContent className="p-4 text-green-900 font-medium">
                🧠 {aiSummary}
              </CardContent>
            </Card>
          </div>
        )}

        {searchInfo && (
          <div className="max-w-4xl mx-auto mb-6">
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200 shadow-sm">
              <CardContent className="p-4 text-blue-900 font-medium">
                {searchInfo}
              </CardContent>
            </Card>
          </div>
        )}

        {detectedColor && (
          <div className="max-w-4xl mx-auto mb-6">
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="p-3 text-purple-800">Detected Color: <strong className="capitalize">{detectedColor}</strong></CardContent>
            </Card>
          </div>
        )}

        {accurateResults.length > 0 && (
          <section className="max-w-7xl mx-auto mb-12">
            <div className="mb-6 text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Best Matches</h2>
              <p className="text-gray-600">Found {accurateResults.length} high-confidence results</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {accurateResults.map((p) => <SearchCard key={p.id} {...p} />)}
            </div>
          </section>
        )}

        {relatedResults.length > 0 && (
          <section className="max-w-7xl mx-auto mb-12">
            <div className="mb-6 text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">You Might Also Like</h2>
              <p className="text-gray-600">Showing {relatedResults.length} related items</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {relatedResults.map((p) => <SearchCard key={p.id} {...p} />)}
            </div>
          </section>
        )}

        {!loading && accurateResults.length === 0 && relatedResults.length === 0 && !error && (
          <div className="max-w-2xl mx-auto text-center py-16">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
              <Search className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-3">Ready to Search</h3>
            <p className="text-gray-600 mb-6">Upload an image, enter text like "blue chair" or "wooden table", or use voice search to find products.</p>
          </div>
        )}
      </div>
    </div>
  );
}


