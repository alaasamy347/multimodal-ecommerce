"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Square } from "lucide-react";

interface SearchCardProps {
  id: number;
  name: string;
  category?: string;
  subCategory?: string;
  image_url?: string;
  score: number;
  color?: string;
  has_3d_model?: boolean;
  model_url?: string | null;
  onViewAR?: (id: number) => void;
  onAddToCart?: () => void;
}

export function SearchCard({
  id,
  name,
  category,
  subCategory,
  image_url,
  score,
  color,
  has_3d_model,
  model_url,
  onViewAR,
  onAddToCart
}: SearchCardProps) {
  const [imageError, setImageError] = useState(false);

  // Debug: Log product data
  useEffect(() => {
    console.log(`Product ${id}:`, {
      name,
      score,
      has_3d_model,
      model_url,
      image_url
    });
  }, [id]);

  // Convert score to percentage (it's already 0-1)
  const scorePercent = Math.round(score * 100);

  const imageUrl = image_url || "/placeholder.jpg";

  return (
    <Card className="group overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border-2 hover:border-blue-300">
      <CardContent className="p-0">
        {/* Image */}
        <div className="relative aspect-square overflow-hidden bg-gray-100">
          {!imageError ? (
            <img
              src={imageUrl}
              alt={name}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              loading="lazy"
              onError={(e) => {
                console.error("Image failed to load:", imageUrl);
                setImageError(true);
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gray-200">
              <div className="text-center p-4">
                <div className="text-4xl mb-2">🪑</div>
                <div className="text-sm text-gray-500">Image not available</div>
              </div>
            </div>
          )}

          {/* Match Score */}
          <div className="absolute top-3 right-3">
            <div
              className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md border ${scorePercent >= 85
                ? "bg-green-500/90 text-white border-green-300"
                : scorePercent >= 70
                  ? "bg-blue-500/90 text-white border-blue-300"
                  : scorePercent >= 50
                    ? "bg-yellow-500/90 text-white border-yellow-300"
                    : "bg-gray-500/90 text-white border-gray-300"
                }`}
            >
              {scorePercent}%
            </div>
          </div>

          {/* AR Badge */}
          {has_3d_model && model_url && (
            <div className="absolute top-3 left-3">
              <div className="px-2 py-1 bg-purple-500/90 text-white rounded-full text-xs font-bold backdrop-blur-md border border-purple-300 flex items-center gap-1">
                <Square className="w-3 h-3" />
                AR
              </div>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-4 space-y-3">
          <h3 className="font-semibold text-gray-900 line-clamp-2 min-h-[3rem] text-base leading-tight">
            {name}
          </h3>

          <div className="flex flex-wrap gap-2">
            {category && (
              <Badge variant="secondary" className="text-xs">
                {category}
              </Badge>
            )}
            {subCategory && subCategory !== category && (
              <Badge variant="outline" className="text-xs">
                {subCategory}
              </Badge>
            )}
            {color && color !== "unknown" && (
              <Badge
                variant="outline"
                className="text-xs capitalize border-purple-300 text-purple-700"
              >
                {color}
              </Badge>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => window.open(imageUrl, "_blank")}
              className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2 text-sm"
            >
              <ExternalLink className="w-4 h-4" />
              View
            </button>

            {has_3d_model && model_url ? (
              <button
                onClick={() => {
                  console.log(`Opening AR for product ${id}, model: ${model_url}`);
                  onViewAR?.(id);
                }}
                className="px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all text-sm"
              >
                <Square className="w-4 h-4" />
                AR
              </button>
            ) : has_3d_model && !model_url ? (
              <button
                disabled
                className="px-4 py-2.5 bg-gray-400 text-white rounded-lg font-medium flex items-center justify-center gap-2 cursor-not-allowed text-sm"
                title="3D model file not found"
              >
                <Square className="w-4 h-4" />
                No Model
              </button>
            ) : null}
          </div>
          
          {onAddToCart && (
            <button onClick={onAddToCart}
              className="flex-1 py-2 bg-violet-600 text-white text-xs rounded-lg hover:bg-violet-700 transition-colors font-medium w-full">
              + Add to Cart
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
