"""
Hybrid retrieval: FAISS vector search + NetworkX graph expansion + reranking.
Optimized for episode diversity with controlled token usage.
"""

import numpy as np
import faiss

from utils.loaders import load_embeddings, load_faiss_index, load_metadata
from services.graph_service import graph_service
from config import (
    VECTOR_TOP_K,
    VECTOR_WEIGHT,
    GRAPH_WEIGHT,
    FINAL_TOP_K,
    SIMILARITY_THRESHOLD,
)


class HybridRetriever:
    """
    Orchestrates the hybrid retrieval pipeline with episode diversity.

    Pipeline:
    1. FAISS vector search with wider net (internal).
    2. Graph expansion for context.
    3. Weighted merge (vector + graph scores).
    4. Smart reranking for maximum episode diversity.
    5. Return top chunks (1-2 per episode) for token efficiency.
    """

    def __init__(self):
        self.embeddings: np.ndarray = load_embeddings()
        self.index: faiss.Index = load_faiss_index()
        self.metadata: list[dict] = load_metadata()
        
        # Validate consistency
        print(f"[Retriever Init] Embeddings: {self.embeddings.shape[0]}, "
              f"Index: {self.index.ntotal}, Metadata: {len(self.metadata)}")
        
        # Count unique episodes
        unique_episodes = set(m["doc_id"] for m in self.metadata)
        print(f"[Retriever Init] Unique episodes: {len(unique_episodes)}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query_embedding: np.ndarray,
        mode: str = "story",
    ) -> list[dict]:
        """
        Run the full hybrid retrieval pipeline with episode diversity.

        Args:
            query_embedding: 1-D numpy array (768,) for the user query.
            mode: "story" or "character".

        Returns:
            A list of dicts (max FINAL_TOP_K), each with 'doc_id', 
            'chunk_index', 'score', and 'text'. Optimized for episode 
            diversity (1-2 chunks per episode).
        """
        # --- Step 1: Vector search (cast wider net internally) ---
        # Retrieve more candidates than we'll return to ensure diversity
        internal_k = max(VECTOR_TOP_K * 3, 30)
        vector_results = self._vector_search(query_embedding, top_k=internal_k)

        # --- Step 2: Graph expansion (limited to top vector results) ---
        # Only expand from top VECTOR_TOP_K to control token usage
        top_vector_indices = [r["chunk_index"] for r in vector_results[:VECTOR_TOP_K]]
        graph_indices = graph_service.expand_context(
            top_vector_indices, self.metadata
        )

        # Build graph results with proximity scores
        graph_results = self._build_graph_results(graph_indices)

        # --- Step 3: Hybrid merge ---
        merged = self._merge(vector_results, graph_results)

        # --- Step 4: Mode-specific filtering ---
        if mode == "character":
            doug_indices = set(
                graph_service.filter_doug_indices(self.metadata)
            )
            merged = [r for r in merged if r["chunk_index"] in doug_indices]

        # --- Step 5: Smart rerank for episode diversity ---
        final = self._smart_rerank(merged, mode)
        
        # Debug: Show episode distribution
        episode_dist = {}
        for r in final:
            ep = r["doc_id"]
            episode_dist[ep] = episode_dist.get(ep, 0) + 1
        print(f"[Retrieval] Returning {len(final)} chunks from "
              f"{len(episode_dist)} episodes: {episode_dist}")
        
        return final

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------
    def _vector_search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = None
    ) -> list[dict]:
        """
        Perform FAISS similarity search returning top-K results.
        
        Args:
            query_embedding: Query vector (768,).
            top_k: Number of results to retrieve (defaults to VECTOR_TOP_K).
        
        Returns:
            List of chunk results with scores.
        """
        if top_k is None:
            top_k = VECTOR_TOP_K
            
        query_vec = query_embedding.reshape(1, -1).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            # Convert L2 distance to similarity score
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + float(dist))
            
            # Filter out very weak matches
            if similarity < SIMILARITY_THRESHOLD * 0.5:
                continue
            
            results.append({
                "chunk_index": int(idx),
                "doc_id": self.metadata[int(idx)]["doc_id"],
                "text": self.metadata[int(idx)].get("text", ""),
                "score": similarity,
            })
        
        return results

    def _build_graph_results(self, graph_indices: list[int]) -> list[dict]:
        """
        Build result dicts from graph expansion indices.
        
        Args:
            graph_indices: List of chunk indices from graph expansion.
        
        Returns:
            List of graph results with default proximity scores.
        """
        graph_results = []
        for gidx in graph_indices:
            if 0 <= gidx < len(self.metadata):
                graph_results.append({
                    "chunk_index": gidx,
                    "doc_id": self.metadata[gidx]["doc_id"],
                    "text": self.metadata[gidx].get("text", ""),
                    "score": 0.5,  # Default graph proximity score
                })
        return graph_results

    def _merge(
        self,
        vector_results: list[dict],
        graph_results: list[dict],
    ) -> list[dict]:
        """
        Merge vector and graph results with weighted scoring.

        Score = (VECTOR_WEIGHT * vector_score) + (GRAPH_WEIGHT * graph_score)
        Duplicates are resolved by keeping the highest combined score.
        
        Args:
            vector_results: Results from FAISS vector search.
            graph_results: Results from graph expansion.
        
        Returns:
            Merged and scored results, sorted by final score.
        """
        combined: dict[int, dict] = {}

        # Add vector results
        for r in vector_results:
            idx = r["chunk_index"]
            combined[idx] = {
                "chunk_index": idx,
                "doc_id": r["doc_id"],
                "text": r.get("text", ""),
                "vector_score": r["score"],
                "graph_score": 0.0,
            }

        # Add or merge graph results
        for r in graph_results:
            idx = r["chunk_index"]
            if idx in combined:
                # Update graph score for existing entry
                combined[idx]["graph_score"] = r["score"]
            else:
                # Add new entry from graph
                combined[idx] = {
                    "chunk_index": idx,
                    "doc_id": r["doc_id"],
                    "text": r.get("text", ""),
                    "vector_score": 0.0,
                    "graph_score": r["score"],
                }

        # Compute final weighted scores
        merged = []
        for entry in combined.values():
            entry["score"] = (
                VECTOR_WEIGHT * entry["vector_score"]
                + GRAPH_WEIGHT * entry["graph_score"]
            )
            merged.append(entry)

        # Sort by final score (highest first)
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged

    def _smart_rerank(
        self, 
        candidates: list[dict], 
        mode: str
    ) -> list[dict]:
        """
        Smart reranking for maximum episode diversity with minimal tokens.
        
        Strategy:
        1. Group chunks by episode.
        2. Prioritize episodes with highest-scoring chunks.
        3. Round-robin selection to ensure we return FINAL_TOP_K chunks.
        
        Args:
            candidates: Merged candidate chunks.
            mode: "story" or "character".
        
        Returns:
            Reranked results with episode diversity (max FINAL_TOP_K).
        """
        if not candidates:
            return []

        # Group chunks by episode
        episode_chunks: dict[str, list[dict]] = {}
        for c in candidates:
            ep = c["doc_id"]
            if ep not in episode_chunks:
                episode_chunks[ep] = []
            episode_chunks[ep].append(c)

        # Sort chunks within each episode by score
        for ep in episode_chunks:
            episode_chunks[ep].sort(key=lambda x: x["score"], reverse=True)

        # Sort episodes by their top chunk's score
        sorted_episodes = sorted(
            episode_chunks.keys(),
            key=lambda ep: episode_chunks[ep][0]["score"],
            reverse=True
        )

        reranked = []
        pointers = {ep: 0 for ep in sorted_episodes}
        
        # Round-robin selection: take 1 chunk from each episode in order of episode rank,
        # then loop back and take the next chunk, until we hit FINAL_TOP_K.
        # This maximizes episode diversity while guaranteeing we return FINAL_TOP_K chunks
        # if enough candidates exist.
        while len(reranked) < FINAL_TOP_K:
            added_this_round = False
            for ep in sorted_episodes:
                if len(reranked) >= FINAL_TOP_K:
                    break
                idx = pointers[ep]
                if idx < len(episode_chunks[ep]):
                    reranked.append(episode_chunks[ep][idx])
                    pointers[ep] += 1
                    added_this_round = True
            
            if not added_this_round:
                break # We've exhausted all available chunks

        return reranked


# Module-level singleton
retriever = HybridRetriever()