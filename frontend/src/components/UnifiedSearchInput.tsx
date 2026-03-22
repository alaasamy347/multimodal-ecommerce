// "use client";

// import { useState, useRef } from "react";

// export function UnifiedSearchInput({ onSearch, loading }: any) {
//   const [query, setQuery] = useState("");
//   const [imageFile, setImageFile] = useState<File | null>(null);
//   const [audioFile, setAudioFile] = useState<File | null>(null);
//   const [recording, setRecording] = useState(false);
//   const [imagePreview, setImagePreview] = useState<string | null>(null);

//   const mediaRecorderRef = useRef<MediaRecorder | null>(null);
//   const audioChunksRef = useRef<Blob[]>([]);
//   const fileInputRef = useRef<HTMLInputElement>(null);

//   // ── Voice Recording ──────────────────────────────────────────
//   async function startRecording() {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//       mediaRecorderRef.current = new MediaRecorder(stream);
//       audioChunksRef.current = [];

//       mediaRecorderRef.current.ondataavailable = (e) => {
//         if (e.data.size > 0) {
//           audioChunksRef.current.push(e.data);
//         }
//       };

//       mediaRecorderRef.current.onstop = () => {
//         const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
//         const file = new File([blob], "query.wav", { type: "audio/wav" });
//         setAudioFile(file);
//         stream.getTracks().forEach((track) => track.stop());
//         mediaRecorderRef.current = null;
//       };

//       mediaRecorderRef.current.start();
//       setRecording(true);
//     } catch (error) {
//       console.error("Microphone access error:", error);
//       alert("Could not access microphone. Please check permissions.");
//     }
//   }

//   function stopRecording() {
//     if (mediaRecorderRef.current && recording) {
//       mediaRecorderRef.current.stop();
//       setRecording(false);
//     }
//   }

//   // ── Image Upload ─────────────────────────────────────────────
//   const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const file = e.target.files?.[0];
//     if (file) {
//       setImageFile(file);
//       const reader = new FileReader();
//       reader.onload = (e) => setImagePreview(e.target?.result as string);
//       reader.readAsDataURL(file);
//     }
//   };

//   const removeImage = () => {
//     setImageFile(null);
//     setImagePreview(null);
//     if (fileInputRef.current) fileInputRef.current.value = "";
//   };

//   const removeAudio = () => {
//     setAudioFile(null);
//   };

//   // ── Submit ───────────────────────────────────────────────────
//   const handleSubmit = (e: React.FormEvent) => {
//     e.preventDefault();
//     if (query.trim() || imageFile || audioFile) {
//       onSearch({ query: query.trim(), image: imageFile, audio: audioFile });
//     }
//   };

//   // Active inputs indicator
//   const activeInputs = [
//     query.trim() && "text",
//     imageFile && "image",
//     audioFile && "voice",
//   ].filter(Boolean);

//   return (
//     <div className="w-full max-w-4xl mx-auto">
//       <form onSubmit={handleSubmit} className="space-y-4">

//         {/* Attachments Preview */}
//         {(imageFile || audioFile) && (
//           <div className="flex flex-wrap gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
//             {imageFile && imagePreview && (
//               <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-gray-300 shadow-sm">
//                 <img
//                   src={imagePreview}
//                   alt="Preview"
//                   className="w-12 h-12 object-cover rounded"
//                 />
//                 <div className="flex flex-col min-w-0">
//                   <span className="text-sm font-medium truncate max-w-[150px]">
//                     {imageFile.name}
//                   </span>
//                   <span className="text-xs text-gray-500">
//                     {Math.round(imageFile.size / 1024)}KB
//                   </span>
//                 </div>
//                 <button
//                   type="button"
//                   onClick={removeImage}
//                   className="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none"
//                   title="Remove image"
//                 >
//                   ×
//                 </button>
//               </div>
//             )}

//             {audioFile && (
//               <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-green-300 shadow-sm">
//                 <div className="w-12 h-12 bg-green-100 rounded flex items-center justify-center text-2xl">
//                   🎤
//                 </div>
//                 <div className="flex flex-col">
//                   <span className="text-sm font-medium">Voice Recording</span>
//                   <span className="text-xs text-gray-500">
//                     {Math.round(audioFile.size / 1024)}KB — ready to search
//                   </span>
//                 </div>
//                 <button
//                   type="button"
//                   onClick={removeAudio}
//                   className="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none"
//                   title="Remove audio"
//                 >
//                   ×
//                 </button>
//               </div>
//             )}
//           </div>
//         )}

//         {/* Combined mode indicator */}
//         {activeInputs.length > 1 && (
//           <div className="flex justify-center">
//             <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">
//               ✨ Combined search: {activeInputs.join(" + ")}
//             </span>
//           </div>
//         )}

//         {/* Main Input Bar */}
//         <div className="bg-white rounded-xl border-2 border-gray-200 shadow-sm hover:border-blue-300 focus-within:border-blue-500 transition-colors">
//           <div className="flex items-center gap-2 p-4">
//             <input
//               value={query}
//               onChange={(e) => setQuery(e.target.value)}
//               placeholder='Search with text, image, voice, or all three... (e.g. "red sofa")'
//               className="flex-1 border-0 bg-transparent text-base outline-none placeholder:text-gray-400"
//               disabled={loading}
//             />

//             {/* Image Upload Button */}
//             <input
//               ref={fileInputRef}
//               type="file"
//               accept="image/*"
//               onChange={handleImageUpload}
//               className="hidden"
//             />
//             <button
//               type="button"
//               onClick={() => fileInputRef.current?.click()}
//               className={`p-2 rounded-lg transition-colors text-xl ${
//                 imageFile
//                   ? "bg-blue-100 text-blue-600"
//                   : "hover:bg-gray-100"
//               }`}
//               title={imageFile ? "Image attached" : "Upload image"}
//               disabled={loading}
//             >
//               📷
//             </button>

//             {/* Voice Recording Button */}
//             {!recording ? (
//               <button
//                 type="button"
//                 onClick={startRecording}
//                 className={`p-2 rounded-lg transition-colors text-xl ${
//                   audioFile
//                     ? "bg-green-100 text-green-600"
//                     : "hover:bg-green-50"
//                 }`}
//                 title={audioFile ? "Voice recorded — click to re-record" : "Start voice recording"}
//                 disabled={loading}
//               >
//                 🎤
//               </button>
//             ) : (
//               <button
//                 type="button"
//                 onClick={stopRecording}
//                 className="p-2 bg-red-50 hover:bg-red-100 rounded-lg transition-colors text-xl animate-pulse"
//                 title="Stop recording"
//               >
//                 ⏹️
//               </button>
//             )}

//             {/* Search Button */}
//             <button
//               type="submit"
//               disabled={loading || (!query.trim() && !imageFile && !audioFile)}
//               className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium whitespace-nowrap"
//             >
//               {loading ? (
//                 <span className="flex items-center gap-2">
//                   <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
//                   Searching...
//                 </span>
//               ) : (
//                 "Search"
//               )}
//             </button>
//           </div>

//           {/* Recording Status Bar */}
//           {recording && (
//             <div className="px-4 pb-3 flex items-center gap-2 border-t border-gray-100 pt-2">
//               <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
//               <span className="text-sm text-red-600 font-medium">
//                 Recording... Click ⏹️ to finish and attach
//               </span>
//             </div>
//           )}

//           {/* Helper hint */}
//           {!recording && (
//             <div className="px-4 pb-3 flex items-center gap-4 text-xs text-gray-400">
//               <span>📝 Type to search</span>
//               <span>📷 Upload image</span>
//               <span>🎤 Record voice</span>
//               <span className="text-purple-400 font-medium">✨ Combine any!</span>
//             </div>
//           )}
//         </div>
//       </form>
//     </div>
//   );
// }



"use client";

import { useState, useRef, useImperativeHandle, forwardRef } from "react";

export function UnifiedSearchInput({ onSearch, loading }: any) {
  const [query, setQuery]               = useState("");
  const [imageFile, setImageFile]       = useState<File | null>(null);
  const [audioFile, setAudioFile]       = useState<File | null>(null);
  const [recording, setRecording]       = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [audioLabel, setAudioLabel]     = useState<string>("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef   = useRef<Blob[]>([]);
  const fileInputRef     = useRef<HTMLInputElement>(null);

  // ── Convert any audio blob → 16kHz mono WAV in browser (no ffmpeg) ──
  async function blobToWav(blob: Blob): Promise<File> {
    const arrayBuffer = await blob.arrayBuffer();
    const audioCtx    = new AudioContext();
    const decoded     = await audioCtx.decodeAudioData(arrayBuffer);
    const targetSr    = 16000;
    const offCtx      = new OfflineAudioContext(1, Math.ceil(decoded.duration * targetSr), targetSr);
    const src         = offCtx.createBufferSource();
    src.buffer        = decoded;
    src.connect(offCtx.destination);
    src.start(0);
    const rendered = await offCtx.startRendering();
    await audioCtx.close();
    const samples  = rendered.getChannelData(0);
    return new File([encodeWav(samples, targetSr)], "recording.wav", { type: "audio/wav" });
  }

  function encodeWav(samples: Float32Array, sr: number): ArrayBuffer {
    const buf  = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buf);
    const str  = (off: number, s: string) => { for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); };
    str(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true);
    str(8, "WAVE"); str(12, "fmt ");
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, sr, true); view.setUint32(28, sr * 2, true);
    view.setUint16(32, 2, true);  view.setUint16(34, 16, true);
    str(36, "data"); view.setUint32(40, samples.length * 2, true);
    let off = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      off += 2;
    }
    return buf;
  }

  // ── Voice Recording ──────────────────────────────────────────
  async function startRecording() {
    try {
      const stream   = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = ["audio/webm;codecs=opus","audio/webm","audio/ogg;codecs=opus","audio/mp4"]
        .find(m => MediaRecorder.isTypeSupported(m)) || "";
      mediaRecorderRef.current = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      audioChunksRef.current   = [];

      mediaRecorderRef.current.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorderRef.current.onstop = async () => {
        const rawBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current?.mimeType || "audio/webm" });
        stream.getTracks().forEach(t => t.stop());
        mediaRecorderRef.current = null;
        try {
          const wav = await blobToWav(rawBlob);
          setAudioFile(wav);
          setAudioLabel(`${Math.round(wav.size / 1024)}KB · WAV 16kHz`);
        } catch {
          const fb = new File(audioChunksRef.current, "recording.webm", { type: rawBlob.type });
          setAudioFile(fb);
          setAudioLabel(`${Math.round(fb.size / 1024)}KB · WEBM`);
        }
      };
      mediaRecorderRef.current.start(100);
      setRecording(true);
    } catch {
      alert("Could not access microphone. Please allow permissions.");
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  }

  // ── Image ────────────────────────────────────────────────────
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = ev => setImagePreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const removeImage = () => { setImageFile(null); setImagePreview(null); if (fileInputRef.current) fileInputRef.current.value = ""; };
  const removeAudio = () => { setAudioFile(null); setAudioLabel(""); };

  // ── Clear everything after submit ────────────────────────────
  function clearAll() {
    setQuery("");
    setImageFile(null);
    setImagePreview(null);
    setAudioFile(null);
    setAudioLabel("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  // ── Submit ───────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() && !imageFile && !audioFile) return;

    // Capture current values before clearing
    const submitData = { query: query.trim(), image: imageFile, audio: audioFile };

    // Clear inputs immediately so UI feels responsive
    clearAll();

    // Fire search
    onSearch(submitData);
  };

  const activeInputs = [query.trim() && "text", imageFile && "image", audioFile && "voice"].filter(Boolean);

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-3">

        {/* Attachments */}
        {(imageFile || audioFile) && (
          <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-xl border border-gray-200">
            {imageFile && imagePreview && (
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-gray-200 shadow-sm">
                <img src={imagePreview} alt="Preview" className="w-10 h-10 object-cover rounded" />
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-medium truncate max-w-[120px]">{imageFile.name}</span>
                  <span className="text-xs text-gray-400">{Math.round(imageFile.size / 1024)}KB</span>
                </div>
                <button type="button" onClick={removeImage} className="text-red-400 hover:text-red-600 font-bold ml-1">×</button>
              </div>
            )}
            {audioFile && (
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-green-200 shadow-sm">
                <div className="w-10 h-10 bg-green-100 rounded flex items-center justify-center text-xl">🎤</div>
                <div className="flex flex-col">
                  <span className="text-xs font-medium">Voice Recording</span>
                  <span className="text-xs text-gray-400">{audioLabel}</span>
                </div>
                <button type="button" onClick={removeAudio} className="text-red-400 hover:text-red-600 font-bold ml-1">×</button>
              </div>
            )}
          </div>
        )}

        {activeInputs.length > 1 && (
          <div className="flex justify-center">
            <span className="inline-flex items-center gap-1 px-3 py-0.5 rounded-full text-xs font-medium bg-violet-100 text-violet-700 border border-violet-200">
              ✨ Combined: {activeInputs.join(" + ")}
            </span>
          </div>
        )}

        {/* Input bar */}
        <div className="bg-white rounded-xl border-2 border-gray-200 focus-within:border-violet-400 transition-colors shadow-sm">
          <div className="flex items-center gap-2 px-3 py-3">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(e as any); } }}
              placeholder='Type, upload image, or record voice...'
              className="flex-1 border-0 bg-transparent text-sm outline-none placeholder:text-gray-400"
              disabled={loading}
            />

            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={loading}
                    className={`p-1.5 rounded-lg text-lg transition-colors ${imageFile ? "bg-blue-100" : "hover:bg-gray-100"}`}
                    title="Upload image">📷</button>

            {!recording ? (
              <button type="button" onClick={startRecording} disabled={loading}
                      className={`p-1.5 rounded-lg text-lg transition-colors ${audioFile ? "bg-green-100" : "hover:bg-green-50"}`}
                      title="Record voice">🎤</button>
            ) : (
              <button type="button" onClick={stopRecording}
                      className="p-1.5 bg-red-50 rounded-lg text-lg animate-pulse" title="Stop">⏹️</button>
            )}

            <button type="submit"
                    disabled={loading || (!query.trim() && !imageFile && !audioFile)}
                    className="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-40 transition-colors text-sm font-medium whitespace-nowrap">
              {loading ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
                  ...
                </span>
              ) : "Search"}
            </button>
          </div>

          {recording && (
            <div className="px-3 pb-2 flex items-center gap-2 text-xs text-red-500">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse inline-block" />
              Recording... click ⏹️ to stop
            </div>
          )}

          {!recording && (
            <div className="px-3 pb-2 flex gap-3 text-xs text-gray-400">
              <span>📝 Type</span><span>📷 Image</span><span>🎤 Voice</span>
              <span className="text-violet-400">✨ Combine!</span>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}