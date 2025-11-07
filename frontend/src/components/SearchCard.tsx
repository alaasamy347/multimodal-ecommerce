"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Maximize2 } from "lucide-react";
import { ARViewer } from "./ARViewer";
// import { ARViewer } from "./ARViewer";

interface SearchCardProps {
  id: string;
  image: string;
  name: string;
  category: string;
  subCategory: string;
  color?: string;
  score: number;
}

export function SearchCard({ id, image, name, category, subCategory, color, score }: SearchCardProps) {
  const [showAR, setShowAR] = useState(false);

  return (
    <>
      <Card className="group overflow-hidden bg-white/50 backdrop-blur-sm border border-gray-200 hover:shadow-lg hover:scale-[1.02] transition-all duration-300">
        <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-gray-100 to-gray-50">
          <img
            src={`http://localhost:8000/static/${image}`}
            alt={name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
            onError={(e) => {
              e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23ddd" width="100" height="100"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="%23999">No Image</text></svg>';
            }}
          />
          
          {/* AR Button Overlay */}
          <button
            onClick={() => setShowAR(true)}
            className="absolute top-2 right-2 p-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all opacity-0 group-hover:opacity-100"
            title="View in AR"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        <CardContent className="p-4 space-y-2">
          <h3 className="font-semibold text-gray-900 truncate text-sm" title={name}>{name}</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{category}</span>
            {subCategory && <span className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">{subCategory}</span>}
            {color && <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded border border-blue-200">{color}</span>}
          </div>
          <div className="flex justify-between items-center text-xs text-gray-600">
            <span>Relevance</span>
            <span className={`font-medium ${score > 0.8 ? "text-green-600" : score > 0.6 ? "text-blue-600" : "text-gray-600"}`}>
              {(score * 100).toFixed(1)}%
            </span>
          </div>

          {/* AR Preview Button */}
          <button
            onClick={() => setShowAR(true)}
            className="w-full mt-2 px-3 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm font-medium"
          >
            <Maximize2 className="w-4 h-4" />
            View in AR
          </button>
        </CardContent>
      </Card>

      {/* AR Modal */}
      {showAR && (
        <ARViewer
          productId={id}
          productName={name}
          onClose={() => setShowAR(false)}
        />
      )}
    </>
  );
}