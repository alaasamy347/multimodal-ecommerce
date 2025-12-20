"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Square } from "lucide-react";
import { ARViewer } from "./ARViewer";

interface SearchCardProps {
  id: number;
  name: string;
  category?: string;
  subCategory?: string;
  image: string;
  score: number;
  color?: string;
  has_3d_model?: boolean;
}

export function SearchCard({
  id,
  name,
  category,
  subCategory,
  image,
  score,
  color,
  has_3d_model,
}: SearchCardProps) {
  const [showAR, setShowAR] = useState(false);
  
  const imageUrl = `${process.env.NEXT_PUBLIC_API_URL}/static/${image}`;
  const scorePercent = Math.round(score * 100);

  return (
    <>
      <Card className="group overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border-2 hover:border-blue-300">
        <CardContent className="p-0">
          {/* Image Container */}
          <div className="relative aspect-square overflow-hidden bg-gray-100">
            <img
              src={imageUrl}
              alt={name}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect fill='%23f0f0f0' width='200' height='200'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23999' font-size='16'%3ENo Image%3C/text%3E%3C/svg%3E";
              }}
            />
            
            {/* Score Badge */}
            <div className="absolute top-3 right-3">
              <div 
                className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md border ${
                  scorePercent >= 85 
                    ? 'bg-green-500/90 text-white border-green-300' 
                    : scorePercent >= 70 
                    ? 'bg-blue-500/90 text-white border-blue-300' 
                    : 'bg-gray-500/90 text-white border-gray-300'
                }`}
              >
                {scorePercent}% Match
              </div>
            </div>

            {/* AR Badge */}
            {has_3d_model && (
              <div className="absolute top-3 left-3">
                <div className="px-2 py-1 bg-purple-500/90 text-white rounded-full text-xs font-bold backdrop-blur-md border border-purple-300 flex items-center gap-1">
                  <Square className="w-3 h-3" />
                  AR
                </div>
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="p-4 space-y-3">
            {/* Name */}
            <h3 className="font-semibold text-gray-900 line-clamp-2 min-h-[3rem] text-base leading-tight">
              {name}
            </h3>

            {/* Tags */}
            <div className="flex flex-wrap gap-2">
              {category && (
                <span 
                // variant="secondary" 
                className="text-xs">
                  {category}
                </span>
              )}
              {subCategory && subCategory !== category && (
                <span
                //  variant="outline" 
                 className="text-xs">
                  {subCategory}
                </span>
              )}
              {color && color !== "unknown" && (
                <span 
                  // variant="outline" 
                  className="text-xs capitalize border-purple-300 text-purple-700"
                >
                  {color}
                </span>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              {/* View Image Button */}
              <button
                onClick={() => window.open(imageUrl, '_blank')}
                className="flex-1 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                View
              </button>

              {/* AR Button */}
              {has_3d_model && (
                <button
                  onClick={() => setShowAR(true)}
                  className="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg transition-all duration-300 hover:scale-[1.02] active:scale-95 flex items-center justify-center gap-2"
                  title="View in AR"
                >
                  <Square className="w-4 h-4" />
                  AR
                </button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AR Viewer Modal */}
      {showAR && (
        <ARViewer
          productId={id.toString()}
          productName={name}
          onClose={() => setShowAR(false)}
        />
      )}
    </>
  );
}