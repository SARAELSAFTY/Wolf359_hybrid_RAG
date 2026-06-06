"""
Hybrid retrieval: FAISS vector search + NetworkX graph expansion + reranking.
"""

import re
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
    1. Clean and normalize query strings (remove metadata noise/prefixes).
    2. Direct short-circuit routing for meta-queries or direct episode lookups.
    3. FAISS vector search with wider net (internal).
    4. Graph expansion for context.
    5. Weighted merge (vector + graph scores).
    6. Smart reranking for maximum episode diversity.
    7. Return top chunks (1-2 per episode) for token efficiency.
    """

    def __init__(self):
        self.embeddings: np.ndarray = load_embeddings()
        self.index: faiss.Index = load_faiss_index()
        self.metadata: list[dict] = load_metadata()
        
        # Validate consistency
        print(f"[Retriever Init] Embeddings: {self.embeddings.shape[0]}, "
              f"Index: {self.index.ntotal}, Metadata: {len(self.metadata)}")
        
        # Count unique episodes
        self.unique_episodes = sorted(list(set(m["episode_id"] for m in self.metadata)))
        print(f"[Retriever Init] Unique episodes: {len(self.unique_episodes)}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def retrieve(
        self,
        query_embedding: np.ndarray,
        query_text: str = "",
        mode: str = "story",
    ) -> list[dict]:
        """
        Run the full hybrid retrieval pipeline with episode diversity.
        """
        # --- Step 0: Clean Query and Short-Circuit Routing ---
        cleaned_text = self._clean_query(query_text)
        

        # Intercept general questions asking what episodes exist
        query_lower = cleaned_text.lower()
        list_triggers = [
            "what episodes",
            "list episodes",
            "list all episodes", 
            "available episodes",
            "show all episodes",
            "show episodes",
            "all episodes",
            "which episodes"
        ]
        
        # Check if this is a listing request
        is_listing_query = any(trigger in query_lower for trigger in list_triggers)
        
        # Also check for simple "list" at start + "episode" anywhere
        if not is_listing_query and query_lower.strip().startswith("list") and "episode" in query_lower:
            is_listing_query = True
            
        if is_listing_query:
            print(f"[Retrieval] Episode listing query detected: '{query_text}'")
            return self._handle_meta_episode_query()

        # Short-circuit: direct episode name match
        episode_hits = self._find_by_episode_name(cleaned_text)
        if episode_hits:
            # If this is a single-episode query, limit chunks to save tokens
            unique_eps = set(r["episode_id"] for r in episode_hits)
            if len(unique_eps) == 1:
                # Return only top 3-5 chunks from this single episode
                episode_hits.sort(key=lambda x: x["score"], reverse=True)
                limited = episode_hits[:5]
                print(f"[Retrieval] Single episode query detected: {list(unique_eps)[0]}, returning {len(limited)} chunks")
                return limited
            return self._smart_rerank(episode_hits, mode)

        # --- Step 1: Vector search (cast wider net internally) ---
        internal_k = max(VECTOR_TOP_K * 3, 20)
        vector_results = self._vector_search(query_embedding, top_k=internal_k)

        # --- Step 2: Graph expansion (limited to top vector results) ---
        top_vector_indices = [r["chunk_index"] for r in vector_results[:VECTOR_TOP_K]]
        graph_indices = graph_service.expand_context(
            top_vector_indices, self.metadata
        )

        # Build graph results with proximity scores
        graph_results = self._build_graph_results(graph_indices)

        # --- Step 3: Hybrid merge ---
        merged = self._merge(vector_results, graph_results)

        # --- Step 4: Smart rerank for episode diversity ---
        final = self._smart_rerank(merged, mode)
        
        # Debug: Show episode distribution
        episode_dist = {}
        for r in final:
            ep = r["episode_id"]
            episode_dist[ep] = episode_dist.get(ep, 0) + 1
        print(f"[Retrieval] Returning {len(final)} chunks from "
              f"{len(episode_dist)} episodes: {episode_dist}")
        
        return final

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------
    def _clean_query(self, query_text: str) -> str:
        """Normalize queries that contain raw metadata syntax or list artifacts."""
        if not query_text:
            return ""
        # Strip JSON-like syntax noise
        query_text = re.sub(r'episode_id["\s:]+', '', query_text)
        # Clean specific LLM enumeration reference patterns: "4 (part of 27. Knock, Knock)" -> "27. Knock, Knock"
        query_text = re.sub(r'^\d+\s*\(part of\s*([^)]+)\)', r'\1', query_text.strip())
        # Strip simple leading index numbers: "1. Succulent" → "Succulent"
        query_text = re.sub(r'^\d+\.\s*', '', query_text.strip())
        return query_text.strip('"').strip()

    def _find_by_episode_name(self, query_text: str) -> list[dict] | None:
        """If query contains an episode name or number, return its chunks directly."""
        if not query_text or len(query_text) < 1:
            return None
            
        query_lower = query_text.lower()
        
        # 1. Try an exact number match (e.g., extracts "1" from "episode 1" or "episode 01")
        episode_num_match = re.search(r'(?:episode|ep)\s*(\d+)', query_lower)
        
        matches = []
        if episode_num_match:
            target_num = episode_num_match.group(1)
            # Pad with a zero if your metadata uses "01" instead of "1"
            padded_num = target_num.zfill(2) 
            
            for i, m in enumerate(self.metadata):
                ep_id = m["episode_id"].lower()
                # Matches if string starts with "1." or "01." or "1 "
                if ep_id.startswith(f"{target_num}.") or ep_id.startswith(f"{padded_num}."):
                    matches.append((i, m))
                    
        # 2. Fallback to substring matching if no direct number was isolated
        if not matches:
            for i, m in enumerate(self.metadata):
                ep_id_lower = m["episode_id"].lower()
                # Extract episode name by removing number prefix
                ep_name = re.sub(r'^\d+\.\s*', '', ep_id_lower).strip()
                if len(ep_name) >= 3 and ep_name in query_lower:
                    matches.append((i, m))
            
        if not matches:
            return None
            
        return [
            {
                "chunk_index": i,
                "episode_id": m["episode_id"],
                "text": m.get("text", ""),
                "score": 1.0,
                "vector_score": 1.0,
                "graph_score": 0.0
            }
            for i, m in matches
        ]
    def _handle_meta_episode_query(self) -> list[dict]:
        """Returns a compact list of all episodes for listing queries."""
        # Return one result per episode with just the episode name
        return [
            {
                "chunk_index": -1,
                "episode_id": ep,
                "text": ep,  # Just the episode name, no extra context
                "score": 1.0,
                "vector_score": 1.0,
                "graph_score": 0.0,
                "is_episode_list": True  # Flag for special handling
            }
            for ep in self.unique_episodes
        ]

    def _vector_search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = None
    ) -> list[dict]:
        """Perform FAISS similarity search returning top-K results."""
        if top_k is None:
            top_k = VECTOR_TOP_K
            
        query_vec = query_embedding.reshape(1, -1).astype("float32")
        distances, indices = self.index.search(query_vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            idx_int = int(idx)
            if idx_int < 0 or idx_int >= len(self.metadata):
                continue
            
            similarity = float(dist)
            if similarity < SIMILARITY_THRESHOLD * 0.5:
                continue
            
            meta_entry = self.metadata[idx_int]
            results.append({
                "chunk_index": idx_int,
                "episode_id": meta_entry["episode_id"],
                "text": meta_entry.get("text", ""),
                "score": similarity,
            })
        
        return results

    def _build_graph_results(self, graph_indices: list[int]) -> list[dict]:
        """Build result dicts from graph expansion indices."""
        graph_results = []
        for gidx in graph_indices:
            if 0 <= gidx < len(self.metadata):
                meta_entry = self.metadata[gidx]
                graph_results.append({
                    "chunk_index": gidx,
                    "episode_id": meta_entry["episode_id"],
                    "text": meta_entry.get("text", ""),
                    "score": 0.5,
                })
        return graph_results

    def _merge(
        self,
        vector_results: list[dict],
        graph_results: list[dict],
    ) -> list[dict]:
        """Merge vector and graph results with unified key mapping and scoring."""
        combined: dict[int, dict] = {}

        # Add vector results
        for r in vector_results:
            idx = r["chunk_index"]
            combined[idx] = {
                "chunk_index": idx,
                "episode_id": r["episode_id"],
                "text": r.get("text", ""),
                "vector_score": r["score"],
                "graph_score": 0.0,
            }

        # Merge graph results
        for r in graph_results:
            idx = r["chunk_index"]
            if idx in combined:
                combined[idx]["graph_score"] = r["score"]
            else:
                combined[idx] = {
                    "chunk_index": idx,
                    "episode_id": r["episode_id"],
                    "text": r.get("text", ""),
                    "vector_score": 0.0,
                    "graph_score": r["score"],
                }

        # Compute combined reciprocal values
        merged = []
        for entry in combined.values():
            entry["score"] = (
                VECTOR_WEIGHT * entry["vector_score"]
                + GRAPH_WEIGHT * entry["graph_score"]
            )
            merged.append(entry)

        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged

    def _smart_rerank(
        self, 
        candidates: list[dict], 
        mode: str
    ) -> list[dict]:
        """Score-decay reranking: balances episode diversity with relevance."""
        if not candidates:
            return []

        # Pass through episode lists without reranking
        if candidates and candidates[0].get("is_episode_list"):
            return candidates

        # Pass through system manifest without reranking
        if len(candidates) == 1 and candidates[0]["episode_id"] == "SYSTEM_MANIFEST":
            return candidates

        pool = [c for c in candidates if c["score"] >= SIMILARITY_THRESHOLD]
        if not pool:
            return []

        # Track how many chunks we've already picked per episode
        episode_selected_count: dict[str, int] = {}
        reranked: list[dict] = []
        diversity_decay = 0.7  # Penalty per already-selected chunk from same episode

        while len(reranked) < FINAL_TOP_K and pool:
            best_idx = -1
            best_penalised = -1.0

            for i, c in enumerate(pool):
                n = episode_selected_count.get(c["episode_id"], 0)
                penalised = c["score"] * (diversity_decay ** n)
                if penalised > best_penalised:
                    best_penalised = penalised
                    best_idx = i

            chosen = pool.pop(best_idx)
            reranked.append(chosen)
            ep = chosen["episode_id"]
            episode_selected_count[ep] = episode_selected_count.get(ep, 0) + 1

        return reranked


# Module-level singleton
retriever = HybridRetriever()