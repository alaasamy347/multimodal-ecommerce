// "use client";

// import { useState } from "react";
// import { Card, CardContent } from "@/components/ui/card";
// import { Maximize2 } from "lucide-react";
// import { ARViewer } from "./ARViewer";
// // import { ARViewer } from "./ARViewer";

// interface SearchCardProps {
//   id: string;
//   image: string;
//   name: string;
//   category: string;
//   subCategory: string;
//   color?: string;
//   score: number;
// }

// export function SearchCard({ id, image, name, category, subCategory, color, score }: SearchCardProps) {
//   const [showAR, setShowAR] = useState(false);

//   return (
//     <>
//       <Card className="group overflow-hidden bg-white/50 backdrop-blur-sm border border-gray-200 hover:shadow-lg hover:scale-[1.02] transition-all duration-300">
//         <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-gray-100 to-gray-50">
//           <img
//             src={`http://localhost:8000/static/${image}`}
//             alt={name}
//             className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
//             onError={(e) => {
//               e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23ddd" width="100" height="100"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="%23999">No Image</text></svg>';
//             }}
//           />
          
//           {/* AR Button Overlay */}
//           <button
//             onClick={() => setShowAR(true)}
//             className="absolute top-2 right-2 p-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all opacity-0 group-hover:opacity-100"
//             title="View in AR"
//           >
//             <Maximize2 className="w-4 h-4" />
//           </button>
//         </div>

//         <CardContent className="p-4 space-y-2">
//           <h3 className="font-semibold text-gray-900 truncate text-sm" title={name}>{name}</h3>
//           <div className="flex items-center gap-2 flex-wrap">
//             <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{category}</span>
//             {subCategory && <span className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded">{subCategory}</span>}
//             {color && <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded border border-blue-200">{color}</span>}
//           </div>
//           <div className="flex justify-between items-center text-xs text-gray-600">
//             <span>Relevance</span>
//             <span className={`font-medium ${score > 0.8 ? "text-green-600" : score > 0.6 ? "text-blue-600" : "text-gray-600"}`}>
//               {(score * 100).toFixed(1)}%
//             </span>
//           </div>

//           {/* AR Preview Button */}
//           <button
//             onClick={() => setShowAR(true)}
//             className="w-full mt-2 px-3 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm font-medium"
//           >
//             <Maximize2 className="w-4 h-4" />
//             View in AR
//           </button>
//         </CardContent>
//       </Card>

//       {/* AR Modal */}
//       {showAR && (
//         <ARViewer
//           productId={id}
//           productName={name}
//           onClose={() => setShowAR(false)}
//         />
//       )}
//     </>
//   );
// }



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