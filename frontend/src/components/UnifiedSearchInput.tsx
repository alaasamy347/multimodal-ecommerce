"use client";

import { useState, useRef } from "react";

// interface UnifiedSearchInputProps {
//   onSearch: (data: {
//     query: string;
//     image: File | null;
//     audio: File | null;
//   }) => void;
//   loading: boolean;
// }

export function UnifiedSearchInput({ onSearch, loading }: any) {
  const [query, setQuery] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [recording, setRecording] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  // FIXED: Use refs to persist across renders
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        const file = new File([blob], "query.wav", { type: "audio/wav" });
        setAudioFile(file);

        // Clean up stream
        stream.getTracks().forEach(track => track.stop());
        mediaRecorderRef.current = null;
      };

      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (error) {
      console.error("Microphone access error:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeAudio = () => {
    setAudioFile(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() || imageFile || audioFile) {
      onSearch({ query: query.trim(), image: imageFile, audio: audioFile });
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Attachments Preview */}
        {(imageFile || audioFile) && (
          <div className="flex flex-wrap gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
            {imageFile && imagePreview && (
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-gray-300 shadow-sm">
                <img src={imagePreview} alt="Preview" className="w-12 h-12 object-cover rounded" />
                <div className="flex flex-col min-w-0">
                  <span className="text-sm font-medium truncate max-w-[150px]">{imageFile.name}</span>
                  <span className="text-xs text-gray-500">{Math.round(imageFile.size / 1024)}KB</span>
                </div>
                <button
                  type="button"
                  onClick={removeImage}
                  className="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none"
                  title="Remove image"
                >
                  ×
                </button>
              </div>
            )}
            {audioFile && (
              <div className="flex items-center gap-2 bg-white rounded-lg p-2 border border-gray-300 shadow-sm">
                <div className="w-12 h-12 bg-green-100 rounded flex items-center justify-center text-2xl">🎤</div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Audio Recording</span>
                  <span className="text-xs text-gray-500">{Math.round(audioFile.size / 1024)}KB</span>
                </div>
                <button
                  type="button"
                  onClick={removeAudio}
                  className="ml-2 text-red-500 hover:text-red-700 font-bold text-lg leading-none"
                  title="Remove audio"
                >
                  ×
                </button>
              </div>
            )}
          </div>
        )}

        {/* Main Input */}
        <div className="bg-white rounded-xl border-2 border-gray-200 shadow-sm hover:border-blue-300 focus-within:border-blue-500 transition-colors">
          <div className="flex items-center gap-2 p-4">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search with text, images, or voice... (e.g., 'red pants', 'blue jacket')"
              className="flex-1 border-0 bg-transparent text-base outline-none placeholder:text-gray-400"
              disabled={loading}
            />

            {/* Image Upload */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-xl"
              title="Upload image"
              disabled={loading}
            >
              📷
            </button>

            {/* Voice Recording */}
            {!recording ? (
              <button
                type="button"
                onClick={startRecording}
                className="p-2 hover:bg-green-50 rounded-lg transition-colors text-xl"
                title="Start recording"
                disabled={loading}
              >
                🎤
              </button>
            ) : (
              <button
                type="button"
                onClick={stopRecording}
                className="p-2 bg-red-50 hover:bg-red-100 rounded-lg transition-colors text-xl animate-pulse"
                title="Stop recording"
              >
                ⏹️
              </button>
            )}

            {/* Search Button */}
            <button
              type="submit"
              disabled={loading || (!query.trim() && !imageFile && !audioFile)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Searching...
                </span>
              ) : (
                "Search"
              )}
            </button>
          </div>

          {/* Recording Status */}
          {recording && (
            <div className="px-4 pb-3 flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-red-600 font-medium">Recording... Click stop (⏹️) to finish</span>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}