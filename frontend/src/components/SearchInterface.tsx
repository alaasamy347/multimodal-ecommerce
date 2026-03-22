// "use client";

// import { useState, useEffect, useRef } from "react";
// import { SearchCard } from "./SearchCard";
// import { ARViewer } from "./ARViewer";
// import { UnifiedSearchInput } from "./UnifiedSearchInput";

// // ── Typewriter hook ───────────────────────────────────────────
// function useTypewriter(text: string, speed = 20) {
//   const [displayed, setDisplayed] = useState("");
//   useEffect(() => {
//     setDisplayed("");
//     if (!text) return;
//     const words = text.split(" ");
//     let i = 0;
//     const t = setInterval(() => {
//       if (i < words.length) {
//         setDisplayed((p) => (p ? p + " " + words[i] : words[i]));
//         i++;
//       } else clearInterval(t);
//     }, speed);
//     return () => clearInterval(t);
//   }, [text]);
//   return displayed;
// }

// // ── Dots animation ────────────────────────────────────────────
// function Dots() {
//   return (
//     <span className="inline-flex gap-1 ml-1 align-middle">
//       {[0, 1, 2].map((i) => (
//         <span key={i} className="w-2 h-2 rounded-full bg-violet-400 inline-block"
//           style={{ animation: `dotpulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
//       ))}
//       <style>{`@keyframes dotpulse{0%,80%,100%{transform:scale(0.6);opacity:0.4}40%{transform:scale(1);opacity:1}}`}</style>
//     </span>
//   );
// }

// // ── AI Bubble ─────────────────────────────────────────────────
// function AIBubble({ text, thinking, isNew }: { text: string; thinking: boolean; isNew: boolean }) {
//   const typed = useTypewriter(isNew ? text : "", 18);
//   const shown = isNew ? typed : text;
//   return (
//     <div className="flex gap-3 items-start">
//       <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg">AI</div>
//       <div className="flex-1 bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-800 text-sm leading-relaxed">
//         {thinking ? (
//           <span className="text-gray-400 italic">Thinking<Dots /></span>
//         ) : (
//           <span>{shown}</span>
//         )}
//       </div>
//     </div>
//   );
// }

// // ── User Bubble ───────────────────────────────────────────────
// function UserBubble({ text, image, voice }: { text?: string; image?: boolean; voice?: string }) {
//   return (
//     <div className="flex gap-3 items-start justify-end">
//       <div className="flex-1 max-w-md">
//         <div className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-sm text-sm leading-relaxed ml-auto">
//           {text && <p>{text}</p>}
//           {image && <p className="opacity-80 mt-1">📷 Image attached</p>}
//           {voice && <p className="opacity-80 mt-1">🎤 Voice: "{voice}"</p>}
//         </div>
//       </div>
//       <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-bold text-sm flex-shrink-0">U</div>
//     </div>
//   );
// }

// // ── Validate voice is a real search query ────────────────────
// async function validateVoiceQuery(transcription: string): Promise<{ valid: boolean; reason: string }> {
//   const FURNITURE_KEYWORDS = [
//     "sofa", "couch", "chair", "table", "desk", "bed", "shelf", "cabinet",
//     "wardrobe", "lamp", "rug", "curtain", "drawer", "bookcase", "stool",
//     "bench", "ottoman", "dresser", "mirror", "furniture", "wooden", "leather",
//     "black", "white", "brown", "gray", "grey", "red", "blue", "green",
//     "want", "need", "find", "search", "show", "looking", "like", "similar",
//     "buy", "price", "cheap", "modern", "vintage", "scandinavian", "small", "large"
//   ];
//   const words = transcription.toLowerCase().split(/\s+/);
//   const matches = words.filter(w => FURNITURE_KEYWORDS.some(k => w.includes(k)));

//   if (matches.length === 0 && transcription.split(" ").length > 4) {
//     return { valid: false, reason: `"${transcription}" doesn't seem to be a furniture search. Please speak clearly near your microphone.` };
//   }
//   return { valid: true, reason: "" };
// }

// // ── Call Claude to interpret search and explain results ───────
// async function callClaude(userIntent: string, results: any[]): Promise<string> {
//   const topResults = results.slice(0, 5).map(r =>
//     `- ${r.name} (${r.color}, score: ${Math.round(r.score * 100)}%)`
//   ).join("\n");

//   const prompt = `You are an AI assistant for a furniture search app. A user searched for: "${userIntent}"

// The search returned these top results:
// ${topResults || "No results found."}

// In 2-3 sentences, naturally explain:
// 1. What you understood they were looking for
// 2. What you found (or didn't find)
// 3. One brief suggestion if results seem off

// Be conversational, helpful, and concise. Don't use bullet points. Sound like a knowledgeable friend.`;

//   try {
//     const res = await fetch("https://api.anthropic.com/v1/messages", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({
//         model: "claude-sonnet-4-20250514",
//         max_tokens: 1000,
//         messages: [{ role: "user", content: prompt }],
//       }),
//     });
//     const data = await res.json();
//     return data.content?.[0]?.text || "I found some results based on your search.";
//   } catch {
//     return `I searched for "${userIntent}" and found ${results.length} results for you.`;
//   }
// }

// // ── Main Component ────────────────────────────────────────────
// export default function SearchInterface() {
//   const [results, setResults]           = useState<any[]>([]);
//   const [loading, setLoading]           = useState(false);
//   const [activeAR, setActiveAR]         = useState<string | null>(null);
//   const [messages, setMessages]         = useState<{ role: string; text: string; image?: boolean; voice?: string; thinking?: boolean; isNew?: boolean }[]>([]);
//   const [showResults, setShowResults]   = useState(false);
//   const [colorFilter, setColorFilter]   = useState<string | null>(null);
//   const [searchMode, setSearchMode]     = useState("");
//   const bottomRef                       = useRef<HTMLDivElement>(null);

//   useEffect(() => {
//     bottomRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages]);

//   const addMsg = (msg: any) =>
//     setMessages((prev) => [...prev, msg]);

//   const updateLast = (update: any) =>
//     setMessages((prev) => {
//       const copy = [...prev];
//       copy[copy.length - 1] = { ...copy[copy.length - 1], ...update };
//       return copy;
//     });

//   async function handleSearch(data: { query: string; image: File | null; audio: File | null }) {
//     const { query, image, audio } = data;
//     if (!query && !image && !audio) return;

//     setLoading(true);
//     setShowResults(false);
//     setResults([]);
//     setColorFilter(null);

//     // Show user message
//     addMsg({ role: "user", text: query, image: !!image, voice: undefined });

//     // Show AI thinking
//     addMsg({ role: "ai", text: "", thinking: true, isNew: false });

//     try {
//       const form = new FormData();
//       form.append("top_k", "20");
//       form.append("query", query || "");
//       if (image) form.append("file", image);
//       if (audio) form.append("audio", audio);

//       const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
//       const res    = await fetch(`${apiUrl}/search/intelligent`, { method: "POST", body: form });

//       if (!res.ok) throw new Error(`Backend error: ${res.status}`);

//       const data2 = await res.json();

//       // Voice validation — reject garbage transcriptions
//       let voiceQuery    = data2.voice_query || "";
//       let voiceRejected = false;

//       if (voiceQuery) {
//         const { valid, reason } = await validateVoiceQuery(voiceQuery);
//         if (!valid) {
//           voiceQuery    = "";
//           voiceRejected = true;
//           // Update user bubble to show voice was rejected
//           setMessages((prev) => {
//             const copy = [...prev];
//             copy[0]    = { ...copy[0], voice: `⚠️ Ignored background noise` };
//             return copy;
//           });
//         } else {
//           // Update user bubble with good voice
//           setMessages((prev) => {
//             const copy = [...prev];
//             copy[0]    = { ...copy[0], voice: voiceQuery };
//             return copy;
//           });
//         }
//       }

//       const allResults   = data2.accurate_results || [];
//       const finalQuery   = voiceRejected
//         ? (query || "furniture")
//         : (data2.interpreted_query || query || voiceQuery || "furniture");

//       setResults(allResults);
//       setColorFilter(data2.color_filter || null);
//       setSearchMode(data2.search_mode || "");

//       // Get Claude interpretation
//       const aiText = await callClaude(finalQuery, allResults);

//       // Replace thinking bubble with real response
//       updateLast({ text: aiText, thinking: false, isNew: true });

//       setShowResults(true);

//     } catch (err: any) {
//       updateLast({
//         text: `Something went wrong: ${err.message}. Make sure the backend is running at localhost:8000.`,
//         thinking: false,
//         isNew: true,
//       });
//     } finally {
//       setLoading(false);
//     }
//   }

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50/30 to-indigo-50/50 flex flex-col">

//       {/* Header */}
//       <div className="text-center pt-10 pb-6 px-4">
//         <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-100 text-violet-700 text-sm font-medium mb-4 border border-violet-200">
//           <span className="w-2 h-2 bg-violet-500 rounded-full animate-pulse" />
//           AI-Powered Furniture Search
//         </div>
//         <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
//           What are you looking for?
//         </h1>
//         <p className="text-gray-500 mt-2 text-base">
//           Describe it, show it, or say it — I'll find it.
//         </p>
//       </div>

//       {/* Chat area */}
//       <div className="flex-1 max-w-3xl w-full mx-auto px-4 pb-4 space-y-4">

//         {/* Welcome message */}
//         {messages.length === 0 && (
//           <div className="flex gap-3 items-start">
//             <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg">AI</div>
//             <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-700 text-sm leading-relaxed max-w-md">
//               Hi! I can help you find furniture by text, image, or voice — or all three at once.
//               Try something like <span className="font-medium text-violet-600">"black leather sofa"</span> or upload a photo of something you like.
//             </div>
//           </div>
//         )}

//         {/* Chat messages */}
//         {messages.map((msg, i) =>
//           msg.role === "user" ? (
//             <UserBubble key={i} text={msg.text} image={msg.image} voice={msg.voice} />
//           ) : (
//             <AIBubble key={i} text={msg.text} thinking={!!msg.thinking} isNew={!!msg.isNew} />
//           )
//         )}

//         {/* Results */}
//         {showResults && results.length > 0 && (
//           <div className="mt-2">
//             {colorFilter && (
//               <div className="flex items-center gap-2 mb-3 text-sm text-violet-700">
//                 <span className="w-3 h-3 rounded-full border-2 border-violet-400"
//                       style={{ background: colorFilter === "gray" ? "#9ca3af" : colorFilter }} />
//                 Filtered by color: <strong className="capitalize">{colorFilter}</strong>
//               </div>
//             )}
//             <div className="flex items-center gap-2 mb-3">
//               <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Results · {results.length} found</span>
//               <div className="flex-1 h-px bg-gray-200" />
//               {searchMode && (
//                 <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
//                   {searchMode}
//                 </span>
//               )}
//             </div>
//             <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
//               {results.slice(0, 12).map((product) => (
//                 <SearchCard
//                   key={product.id}
//                   id={product.id}
//                   name={product.name}
//                   category={product.category}
//                   subCategory={product.subCategory}
//                   image_url={product.image_url}
//                   score={product.score}
//                   color={product.color}
//                   has_3d_model={product.has_3d_model}
//                   model_url={product.model_url}
//                   onViewAR={(id) => setActiveAR(String(id))}
//                 />
//               ))}
//             </div>
//           </div>
//         )}

//         {/* No results */}
//         {showResults && results.length === 0 && (
//           <div className="text-center py-8 text-gray-400 text-sm">
//             No matching products found. Try different keywords or upload an image.
//           </div>
//         )}

//         <div ref={bottomRef} />
//       </div>

//       {/* Search input — fixed at bottom */}
//       <div className="sticky bottom-0 bg-white/80 backdrop-blur border-t border-gray-200 px-4 py-4">
//         <div className="max-w-3xl mx-auto">
//           <UnifiedSearchInput onSearch={handleSearch} loading={loading} />
//         </div>
//       </div>

//       {activeAR && (
//         <ARViewer productId={activeAR} onClose={() => setActiveAR(null)} />
//       )}
//     </div>
//   );
// }



"use client";

import { useState, useEffect, useRef } from "react";
import { SearchCard } from "./SearchCard";
import { ARViewer } from "./ARViewer";
import { UnifiedSearchInput } from "./UnifiedSearchInput";
import { CartDrawer } from "./CartDrawer";
// import { CheckoutPage } from "./CheckoutPage";
import { OrderConfirmation } from "./OrderConfirmation";
import { useCart } from "@/hooks/useCart";
import { CheckoutPage } from "@/app/checkout/page";

// ── Typewriter ────────────────────────────────────────────────
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
      if (key.current !== myKey) { clearInterval(t); return; }
      if (i < words.length) { setDisplayed(p => p ? p + " " + words[i] : words[i]); i++; }
      else clearInterval(t);
    }, speed);
    return () => clearInterval(t);
  }, [text]);
  return displayed;
}

function Dots() {
  return (
    <span className="inline-flex gap-1 ml-1 align-middle">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-2 h-2 rounded-full bg-violet-400 inline-block"
          style={{ animation: `dp 1.2s ease-in-out ${i * 0.2}s infinite` }} />
      ))}
      <style>{`@keyframes dp{0%,80%,100%{transform:scale(0.5);opacity:0.3}40%{transform:scale(1);opacity:1}}`}</style>
    </span>
  );
}

// ── AI summary ────────────────────────────────────────────────
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
  const label = corrected && corrected !== q ? corrected : (vq || q || "your query");
  const count = results?.length ?? 0;

  if (ve && ve.toLowerCase().includes("noise")) {
    return q
      ? `I caught background audio that wasn't a search query — I ignored it. I used your text "${q}" instead and found ${count} result${count !== 1 ? "s" : ""}.`
      : `I caught background audio that wasn't a search query. Try speaking closer to your mic, or type below.`;
  }

  const topScore = results?.[0] ? Math.round((results[0].score ?? 0) * 100) : 0;
  const lowConf = count > 0 && topScore < 65;

  if (count === 0) {
    const tip = cf
      ? `Try removing the color filter, or use a broader term like "sofa" or "chair".`
      : `I couldn't find an exact match. Check your spelling, or try a more common term — like "wardrobe" instead of "wardobe". You can also upload a photo.`;
    return `I searched for "${label}" but couldn't find any matching items in the catalog. ${tip}`;
  }

  if (lowConf) {
    return `I searched for "${label}" but the catalog doesn't have a strong match. The closest items are shown below, but they may not be exactly right. Try rephrasing — like "wardrobe", "closet", or "storage cabinet" — or upload a photo of what you have in mind.`;
  }

  const parts: string[] = [];
  if (vq && q) parts.push(`I combined your voice "${vq}" with your text "${q}".`);
  else if (vq) parts.push(`I heard "${vq}" from your voice recording.`);
  else if (hasImage && q) parts.push(`I matched your image with the description "${q}".`);
  else if (hasImage) parts.push(`I searched for items visually similar to your image.`);
  else parts.push(`I searched for "${q}".`);

  if (corrected && corrected !== q) parts.push(`(auto-corrected "${q}" to "${corrected}")`);

  const colorNote = cf ? ` in ${cf}` : "";
  if (count >= 15) parts.push(`Found ${count} strong matches${colorNote} — here are the best ones.`);
  else if (count >= 5) parts.push(`Found ${count} good results${colorNote} for you.`);
  else parts.push(`Found ${count} result${count > 1 ? "s" : ""}${colorNote} — limited options for this.`);

  return parts.join(" ");
}


// ── Bubbles ───────────────────────────────────────────────────
function UserBubble({ text, hasImage, imagePreview, voiceQuery, voiceError }: any) {
  return (
    <div className="flex gap-3 items-start justify-end">
      <div className="max-w-sm w-full">
        <div className="bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow text-sm leading-relaxed">
          {text && <p>{text}</p>}
          {imagePreview && (
            <div className="mt-2">
              <img src={imagePreview} alt="Attached" className="rounded-xl max-h-48 max-w-full object-cover border-2 border-white/30" />
            </div>
          )}
          {hasImage && !imagePreview && <p className="opacity-75 text-xs mt-1">📷 Image attached</p>}
          {voiceQuery && !voiceError && <p className="opacity-80 text-xs mt-1">🎤 Heard: "{voiceQuery}"</p>}
          {voiceError && <p className="opacity-60 text-xs mt-1">🎤 Background noise — ignored</p>}
        </div>
      </div>
      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-bold flex-shrink-0">U</div>
    </div>
  );
}

function AIBubble({ text, thinking, animate }: { text: string; thinking?: boolean; animate?: boolean }) {
  const typed = useTypewriter(animate ? text : "", 20);
  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 shadow">AI</div>
      <div className="flex-1 bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-sm border border-gray-100 text-gray-700 text-sm leading-relaxed max-w-lg">
        {thinking ? <span className="text-gray-400 italic text-xs">Searching<Dots /></span>
          : <span>{animate ? typed : text}</span>}
      </div>
    </div>
  );
}

interface ChatEntry {
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

// ── Main ──────────────────────────────────────────────────────
export default function SearchInterface() {
  const [chat, setChat] = useState<ChatEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeAR, setActiveAR] = useState<string | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [screen, setScreen] = useState<Screen>("search");
  const [orderId, setOrderId] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const { totalItems, addItem } = useCart();

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

  const push = (e: ChatEntry) => setChat(p => [...p, e]);
  const patch = (u: Partial<ChatEntry>) =>
    setChat(p => { const c = [...p]; c[c.length - 1] = { ...c[c.length - 1], ...u }; return c; });

  async function handleSearch(data: { query: string; image: File | null; audio: File | null }) {
    const { query, image, audio } = data;
    if (!query && !image && !audio) return;
    setLoading(true);

    let imagePreview: string | undefined;
    if (image) {
      try {
        imagePreview = await new Promise<string>(res => {
          const r = new FileReader(); r.onload = e => res(e.target?.result as string); r.readAsDataURL(image);
        });
      } catch { /* ignore */ }
    }

    push({ type: "user", text: query, hasImage: !!image, imagePreview });
    push({ type: "ai", thinking: true });

    try {
      const form = new FormData();
      form.append("top_k", "20");
      form.append("query", query || "");
      if (image) form.append("file", image);
      if (audio) form.append("audio", audio);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/search/intelligent`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`Backend error ${res.status}`);

      const d = await res.json();
      const results = d.accurate_results || [];
      const voiceQuery = d.voice_query || "";
      const voiceError = d.voice_error || null;
      const colorFilter = d.color_filter || null;
      const searchMode = d.search_mode || "";

      setChat(p => {
        const c = [...p];
        for (let i = c.length - 1; i >= 0; i--) {
          if (c[i].type === "user") { c[i] = { ...c[i], voiceQuery, voiceError }; break; }
        }
        return c;
      });

      const corrected = d.corrected_query || undefined;
      const summary = generateAISummary(query, voiceQuery, voiceError, results, colorFilter, !!imagePreview, corrected);
      patch({ thinking: false, text: summary, animate: true });
      if (results.length > 0) push({ type: "results", results, color: colorFilter, mode: searchMode });

    } catch (err: any) {
      patch({ thinking: false, text: `Something went wrong: ${err.message}`, animate: true });
    } finally {
      setLoading(false);
    }
  }

  if (screen === "checkout") return (
    <CheckoutPage onBack={() => setScreen("search")}
      onSuccess={id => { setOrderId(id); setScreen("confirmation"); }} />
  );
  if (screen === "confirmation") return (
    <OrderConfirmation orderId={orderId} onContinue={() => { setChat([]); setScreen("search"); }} />
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-violet-50/20 to-indigo-50/40 flex flex-col">

      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-8 pb-2 flex-shrink-0">
        <div className="flex-1 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-violet-100 text-violet-700 text-xs font-semibold mb-2 border border-violet-200 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 bg-violet-500 rounded-full animate-pulse" />
            AI Furniture Search
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 tracking-tight">What are you looking for?</h1>
          <p className="text-gray-400 mt-1 text-sm">Describe it · show it · say it</p>
        </div>
        <button onClick={() => setCartOpen(true)}
          className="relative flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl shadow-sm hover:border-violet-300 transition-all text-sm font-medium text-gray-700 flex-shrink-0">
          🛒 Cart
          {totalItems > 0 && (
            <span className="absolute -top-2 -right-2 w-5 h-5 bg-violet-600 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {totalItems}
            </span>
          )}
        </button>
      </div>

      {/* Chat */}
      <div className="flex-1 max-w-3xl w-full mx-auto px-4 pb-6 space-y-5">
        {chat.length === 0 && (
          <AIBubble text={`Hi! I can find furniture for you using text, images, or voice — or all three at once. Try something like "black leather sofa" or upload a photo of a style you like.`} animate={false} />
        )}

        {chat.map((entry, i) => {
          if (entry.type === "user") return (
            <UserBubble key={i} text={entry.text} hasImage={entry.hasImage}
              imagePreview={entry.imagePreview} voiceQuery={entry.voiceQuery} voiceError={entry.voiceError} />
          );
          if (entry.type === "ai") return (
            <AIBubble key={i} text={entry.text || ""} thinking={entry.thinking} animate={entry.animate} />
          );
          if (entry.type === "results" && entry.results) return (
            <div key={i} className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400 uppercase tracking-wider font-semibold">{entry.results.length} Results</span>
                <div className="flex-1 h-px bg-gray-200" />
                {entry.color && (
                  <span className="flex items-center gap-1.5 text-xs text-violet-700 font-medium">
                    <span className="w-3 h-3 rounded-full border border-violet-300 inline-block"
                      style={{ background: entry.color === "gray" ? "#9ca3af" : entry.color === "navy" ? "#1e3a5f" : entry.color }} />
                    {entry.color}
                  </span>
                )}
                {entry.mode && <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-600 font-medium">{entry.mode}</span>}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {entry.results.slice(0, 12).map(p => (
                  <SearchCard
                    key={p.id} id={p.id} name={p.name} category={p.category}
                    subCategory={p.subCategory} image_url={p.image_url}
                    score={p.score} color={p.color}
                    has_3d_model={p.has_3d_model} model_url={p.model_url}
                    onViewAR={(id: any) => setActiveAR(String(id))}
                    onAddToCart={() => addItem({
                      id: p.id, name: p.name, category: p.category,
                      color: p.color, image_url: p.image_url, score: p.score,
                    })}
                  />
                ))}
              </div>
            </div>
          );
          return null;
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="sticky bottom-0 bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="max-w-3xl mx-auto">
          <UnifiedSearchInput onSearch={handleSearch} loading={loading} />
        </div>
      </div>

      <CartDrawer open={cartOpen} onClose={() => setCartOpen(false)}
        onCheckout={() => { setCartOpen(false); setScreen("checkout"); }} />
      {activeAR && <ARViewer productId={activeAR} onClose={() => setActiveAR(null)} />}
    </div>
  );
}