// // frontend/src/lib/evaluationMetrics.ts
// // ══════════════════════════════════════════════════════════════
// // Evaluation Metrics Library for MULTIVIEW Research
// // Implements standard Information Retrieval metrics
// // ══════════════════════════════════════════════════════════════

// export interface SearchResult {
//   id: number;
//   score: number;
//   category: string;
//   relevant?: boolean; // Ground truth relevance (user feedback)
// }

// export interface EvaluationMetrics {
//   precisionAt5: number;
//   precisionAt10: number;
//   recallAt5: number;
//   recallAt10: number;
//   ndcgAt10: number;
//   meanReciprocalRank: number;
// }

// /**
//  * Calculate Precision@K
//  * Definition: (# relevant results in top K) / K
//  * 
//  * Example: If top 5 results have 3 relevant items → P@5 = 3/5 = 0.60
//  */
// export function precisionAtK(results: SearchResult[], k: number): number {
//   if (results.length === 0) return 0;
//   const topK = results.slice(0, k);
//   const relevant = topK.filter(r => r.relevant === true).length;
//   return relevant / k;
// }

// /**
//  * Calculate Recall@K
//  * Definition: (# relevant results in top K) / (total # relevant in full set)
//  * 
//  * Example: If 8 total relevant items exist and 5 appear in top 10 → R@10 = 5/8 = 0.625
//  */
// export function recallAtK(results: SearchResult[], k: number): number {
//   const totalRelevant = results.filter(r => r.relevant === true).length;
//   if (totalRelevant === 0) return 0;
  
//   const topK = results.slice(0, k);
//   const relevantInTopK = topK.filter(r => r.relevant === true).length;
//   return relevantInTopK / totalRelevant;
// }

// /**
//  * Calculate NDCG@K (Normalized Discounted Cumulative Gain)
//  * Measures ranking quality with position-based discounting
//  * 
//  * Higher-ranked relevant items contribute more to the score
//  */
// export function ndcgAtK(results: SearchResult[], k: number): number {
//   const topK = results.slice(0, k);
  
//   // DCG = Σ (relevance / log2(position + 1))
//   const dcg = topK.reduce((sum, result, idx) => {
//     const relevance = result.relevant ? 1 : 0;
//     const position = idx + 1;
//     return sum + relevance / Math.log2(position + 1);
//   }, 0);
  
//   // IDCG (ideal DCG - all relevant items ranked first)
//   const relevantCount = results.filter(r => r.relevant).length;
//   const idcg = Array.from({ length: Math.min(k, relevantCount) })
//     .reduce((sum, _, idx) => sum + 1 / Math.log2(idx + 2), 0);
  
//   return idcg > 0 ? dcg / idcg : 0;
// }

// /**
//  * Calculate Mean Reciprocal Rank
//  * Definition: 1 / (position of first relevant result)
//  * 
//  * Example: First relevant result at position 3 → MRR = 1/3 = 0.333
//  */
// export function meanReciprocalRank(results: SearchResult[]): number {
//   const firstRelevantIdx = results.findIndex(r => r.relevant === true);
//   return firstRelevantIdx >= 0 ? 1 / (firstRelevantIdx + 1) : 0;
// }

// /**
//  * Calculate all metrics at once
//  */
// export function calculateMetrics(results: SearchResult[]): EvaluationMetrics {
//   return {
//     precisionAt5: precisionAtK(results, 5),
//     precisionAt10: precisionAtK(results, 10),
//     recallAt5: recallAtK(results, 5),
//     recallAt10: recallAtK(results, 10),
//     ndcgAt10: ndcgAtK(results, 10),