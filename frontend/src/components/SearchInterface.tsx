"use client";

import { useState, useEffect, useRef } from "react";
import { SearchCard } from "./SearchCard";
import { ARViewer } from "./ARViewer";
import { UnifiedSearchInput } from "./UnifiedSearchInput";
import { ImageGenerator } from "./ImageGenerator";
import { CartDrawer } from "./CartDrawer";
import { OrderConfirmation } from "./OrderConfirmation";
import { useCart } from "@/hooks/useCart";
import { CheckoutPage } from "@/app/checkout/page";

// ── Types ──────────────────────────────────────────────────
interface SearchSession {
  id: string;
  timestamp: number;
  query: string;
  mode: string;
  resultCount: number;
  topScore: number;
  timeMs: number;
  relevant: boolean | null;
  addedToCart: boolean;
  colorFilter: string | null;
  voiceQuery: string | null;
  voiceError: string | null;
  modalities: string[];
}

interface ChatMessage {
  type: "user" | "ai" | "results";
  text?: string;
  hasImage?: boolean;
  imagePreview?: string;
  voiceQuery?: string;
  voiceError?: string;
  thinking?: boolean;
  animate?: boolean;
  results?: any[];
  color?: string | null;
  mode?: string;
}

type Screen = "search" | "checkout" | "confirmation";

// ── Typewriter ────────────────────────────────────────────
function useTypewriter(text: string, speed = 22) {
  const [displayed, setDisplayed] = useState("");
  const key = useRef(0);
  
  useEffect(() => {
    const myKey = ++key.current;
    setDisplayed("");
    if (!text) return;
    
    const words = text.split(" ");
    let i = 0;
    const t = setInterval(() => {
      if (key.current !== myKey) {
        clearInterval(t);
        return;
      }
      if (i < words.length) {
        setDisplayed((p) => (p ? p + " " + words[i] : words[i]));
        i++;
      } else {
        clearInterval(t);
      }
    }, speed);
    
    return () => clearInterval(t);
  }, [text]);
  
  return displayed;
}

function Dots() {
  return (
    <span className="inline-flex gap-1 ml-1 align-middle">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-violet-400 inline-block"
          style={{ animation: `dp 1.2s ease-in-out ${i * 0.2}s infinite` }}
        />
      ))}
      <style>{`@keyframes dp{0%,80%,100%{transform:scale(0.5);opacity:0.3}40%{transform:scale(1);opacity:1}}`}</style>
    </span>
  );
}

// ── AI Response Generation ────────────────────────────────
function generateAISummary(
  query: string | undefined,
  voiceQuery: string | undefined,
  voiceError: string | null | undefined,
  results: any[],
  colorFilter: string | null | undefined,
  hasImage: boolean,
  corrected?: string,
): string {
  const q = (query || "").trim();
  const vq = (voiceQuery || "").trim();
  const ve = voiceError || null;
  const cf = colorFilter || null;
  const label = corrected && corrected !== q ? corrected : vq || q || "your query";
  const count = results?.length ?? 0;

  // Voice error handling
  if (ve && ve.toLowerCase().includes("noise")) {
    return q
      ? `I noticed some background noise in your voice recording, so I used your text "${q}" instead. Found ${count} result${count !== 1 ? "s" : ""} for you.`
      : `I heard some background noise but couldn't quite catch your search. Could you try speaking again or typing your request?`;
  }

  const topScore = results?.[0] ? Math.round((results[0].score ?? 0) * 100) : 0;
  const lowConf = count > 0 && topScore < 60;
  const colorMatches = results.filter(r => r.color?.toLowerCase() === cf?.toLowerCase()).length;

  // No results at all
  if (count === 0) {
    if (cf) {
      return `I searched for "${label}" but I couldn't find any items in ${cf}. Try removing the color filter or searching for a different style.`;
    }
    return `I couldn't find any items matching "${label}". Try using broader terms like "sofa" or "chair", or upload a photo of what you're looking for.`;
  }

  // Build response parts
  const parts: string[] = [];
  
  if (vq && q) {
    parts.push(`I've combined your voice request for "${vq}" with your text "${q}".`);
  } else if (vq) {
    parts.push(`I heard you looking for "${vq}".`);
  } else if (hasImage && q) {
    parts.push(`I've analyzed your image and matched it with the description "${q}".`);
  } else if (hasImage) {
    parts.push(`I've found items that are visually similar to your photo.`);
  } else {
    parts.push(`I found several matches for "${q}".`);
  }

  if (cf) {
    if (colorMatches === 0) {
      parts.push(`I couldn't find any items exactly in ${cf}, so I'm showing you the most similar styles in other colors.`);
    } else {
      parts.push(`I've prioritized items in ${cf} for you.`);
    }
  }

  if (lowConf) {
    parts.push(`The matches aren't perfect, but these are the closest items in our catalog.`);
  } else {
    parts.push(`Here are the best matches I found.`);
  }

  return parts.join(" ");
}

// ── Chat Bubbles ───────────────────────────────────────────
function UserBubble({
  text,
  hasImage,
  imagePreview,
  voiceQuery,
  voiceError,
}: any) {
  return (
    <div className="flex gap-3 items-start justify-end">
      <div className="max-w-sm w-full">
        <div className="bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow text-sm leading-relaxed">
          {text && <p>{text}</p>}
          {imagePreview && (
            <div className="mt-2">
              <img
                src={imagePreview}
                alt="Attached"
                className="rounded-xl max-h-48 max-w-full object-cover border-2 border-white/30"
              />
            </div>
          )}
          {hasImage && !imagePreview && (
            <p className="opacity-75 text-xs mt-1">📷 Image attached</p>
          )}
          {voiceQuery && !voiceError && (
            <p className="opacity-80 text-xs mt-1">🎤 Heard: "{voiceQuery}"</p>
          )}
          {voiceError && (
            <p className="opacity-60 text-xs mt-1">🎤 {voiceError}</p>
          )}
        </div>
      </div>
      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-bold flex-shrink-0">
        U
      </div>
    </div>
  );
}

function AIBubble({
  text,
  thinking,
  animate,
}: {
  text: string;
  thinking?: boolean;
  animate?: boolean;
}) {
  const typed = useTypewriter(animate ? text : "", 20);
  
  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 shadow">
        AI
      </div>
      <div className="flex-1 bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-700 text-sm leading-relaxed max-w-lg">
        {thinking ? (
          <span className="text-gray-400 italic text-xs">
            Searching<Dots />
          </span>
        ) : (
          <span>{animate ? typed : text}</span>
        )}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────
export default function SearchInterface() {
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeAR, setActiveAR] = useState<string | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [screen, setScreen] = useState<Screen>("search");
  const [orderId, setOrderId] = useState("");
  const [showGenerator, setShowGenerator] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const { totalItems, addItem, sessionId } = useCart();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const push = (e: ChatMessage) => setChat((p) => [...p, e]);
  const patch = (u: Partial<ChatMessage>) =>
    setChat((p) => {
      const c = [...p];
      c[c.length - 1] = { ...c[c.length - 1], ...u };
      return c;
    });

  async function handleSearch(data: {
    query: string;
    images: File[];
    audio: File | null;
  }) {
    const { query, images, audio } = data;
    if (!query && images.length === 0 && !audio) return;

    setLoading(true);
    const startTime = Date.now();

    let imagePreview: string | undefined;
    if (images.length > 0) {
      try {
        imagePreview = await new Promise<string>((res) => {
          const r = new FileReader();
          r.onload = (e) => res(e.target?.result as string);
          r.readAsDataURL(images[0]);
        });
      } catch {
        /* ignore */
      }
    }

    push({
      type: "user",
      text: query,
      hasImage: images.length > 0,
      imagePreview,
    });
    push({ type: "ai", thinking: true });

    try {
      const form = new FormData();
      form.append("top_k", "20");
      form.append("query", query || "");
      form.append("session_id", sessionId);
      images.forEach((img) => form.append("image", img));
      if (audio) form.append("audio", audio);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/search/intelligent`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error(`Backend error ${res.status}`);

      const d = await res.json();
      const results = d.accurate_results || [];
      const aiSummary = d.ai_summary || "";
      const voiceQuery = d.voice_query || "";
      const voiceError = d.voice_error || null;
      const colorFilter = d.color_filter || null;
      const searchMode = d.search_mode || "";
      const corrected = d.corrected_query || undefined;
      const responseTime = Date.now() - startTime;

      // Update user bubble with voice info
      setChat((p) => {
        const c = [...p];
        const lastIdx = c.length - 2;
        if (lastIdx >= 0 && c[lastIdx].type === "user") {
          c[lastIdx] = { ...c[lastIdx], voiceQuery, voiceError };
        }
        return c;
      });

      const summary = aiSummary || generateAISummary(
        query,
        voiceQuery,
        voiceError,
        results,
        colorFilter,
        !!imagePreview,
        corrected
      );

      patch({
        thinking: false,
        text: summary,
        animate: true,
      });

      if (results.length > 0) {
        push({
          type: "results",
          results,
          color: colorFilter,
          mode: searchMode,
        });
      }

      // Log session for evaluation
      console.log({
        sessionId,
        query,
        voiceQuery,
        voiceError,
        mode: searchMode,
        results: results.length,
        topScore: results[0]?.score || 0,
        responseTime,
      });
    } catch (err: any) {
      patch({
        thinking: false,
        text: `Something went wrong: ${err.message}. Make sure the backend is running.`,
        animate: true,
      });
    } finally {
      setLoading(false);
    }
  }

  const handleGenerateComplete = async (imageUrl: string, prompt: string) => {
    setShowGenerator(false);
    setLoading(true);
    patch({
      thinking: true,
      text: "Nice design! Finding similar items in our catalog...",
    });

    try {
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const file = new File([blob], `generated_${Date.now()}.jpg`, { type: blob.type });
      
      // Add the AI message showing what was generated
      push({
        type: "ai",
        text: `Here is the furniture I generated to match your idea: "${prompt}"`,
        animate: true,
      });

      // Inject the generated image in the chat flow
      push({
        type: "user",
        text: `(Use this generated image for search)`,
        hasImage: true,
        imagePreview: imageUrl,
      });

      // Pass it directly to handleSearch
      handleSearch({ query: "", images: [file], audio: null });
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  if (screen === "checkout") {
    return (
      <CheckoutPage
        onBack={() => setScreen("search")}
        onSuccess={(id) => {
          setOrderId(id);
          setScreen("confirmation");
        }}
      />
    );
  }

  if (screen === "confirmation") {
    return (
      <OrderConfirmation
        orderId={orderId}
        onContinue={() => {
          setChat([]);
          setScreen("search");
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50/20 to-indigo-50/40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-8 pb-2 flex-shrink-0">
        <div className="flex-1 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-100 text-violet-700 text-xs font-semibold mb-2 border border-violet-200 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-pulse" />
            AI Furniture Search
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">
            What are you looking for?
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Describe it · show it · say it
          </p>
        </div>
        <button
          onClick={() => setCartOpen(true)}
          className="relative flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl shadow-sm hover:border-violet-300 transition-all text-sm font-medium text-gray-700 flex-shrink-0"
        >
          🛒 Cart
          {totalItems > 0 && (
            <span className="absolute -top-2 -right-2 w-5 h-5 bg-violet-600 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {totalItems}
            </span>
          )}
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 pb-6 space-y-5">
        {chat.length === 0 && (
          <AIBubble
            text="Hi! I can find furniture for you using text, images, or voice — or all three at once. Try something like 'black leather sofa' or upload a photo of a style you like."
            animate={false}
          />
        )}

        {chat.map((entry, i) => {
          if (entry.type === "user") {
            return (
              <UserBubble
                key={i}
                text={entry.text}
                hasImage={entry.hasImage}
                imagePreview={entry.imagePreview}
                voiceQuery={entry.voiceQuery}
                voiceError={entry.voiceError}
              />
            );
          }

          if (entry.type === "ai") {
            return (
              <AIBubble
                key={i}
                text={entry.text || ""}
                thinking={entry.thinking}
                animate={entry.animate}
              />
            );
          }

          if (entry.type === "results" && entry.results) {
            return (
              <div key={i} className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">
                    {entry.results.length} Results
                  </span>
                  <div className="flex-1 h-px bg-gray-200" />
                  {entry.color && (
                    <span className="flex items-center gap-1.5 text-xs text-violet-700 font-medium">
                      <span
                        className="w-3 h-3 rounded-full border border-violet-300 inline-block"
                        style={{
                          background:
                            entry.color === "gray"
                              ? "#9ca3af"
                              : entry.color === "navy"
                                ? "#1e3a5f"
                                : entry.color,
                        }}
                      />
                      {entry.color}
                    </span>
                  )}
                  {entry.mode && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 font-medium">
                      {entry.mode}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {entry.results.slice(0, 12).map((p) => (
                    <SearchCard
                      key={p.id}
                      id={p.id}
                      name={p.name}
                      category={p.category}
                      subCategory={p.subCategory}
                      image_url={p.image_url}
                      score={p.score}
                      color={p.color}
                      has_3d_model={p.has_3d_model}
                      model_url={p.model_url}
                      onViewAR={(id: any) => setActiveAR(String(id))}
                      onAddToCart={() =>
                        addItem({
                          id: Number(p.id),
                          name: p.name,
                          category: p.category,
                          color: p.color,
                          image_url: p.image_url,
                          score: p.score,
                        })
                      }
                    />
                  ))}
                </div>
              </div>
            );
          }

          return null;
        })}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="sticky bottom-0 bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="max-w-3xl mx-auto flex flex-col items-center">
          <UnifiedSearchInput onSearch={handleSearch} loading={loading} />
          <button 
            onClick={() => setShowGenerator(true)}
            className="mt-3 text-xs font-semibold text-violet-600 hover:text-violet-800 transition-colors flex items-center gap-1"
          >
            ✨ Having trouble finding it? Generate it with AI!
          </button>
        </div>
      </div>

      {/* Modals */}
      {showGenerator && (
        <ImageGenerator 
          onGenerateComplete={handleGenerateComplete}
          onCancel={() => setShowGenerator(false)}
        />
      )}
      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        onCheckout={() => {
          setCartOpen(false);
          setScreen("checkout");
        }}
      />
      {activeAR && (
        <ARViewer productId={activeAR} onClose={() => setActiveAR(null)} />
      )}
    </div>
  );
}