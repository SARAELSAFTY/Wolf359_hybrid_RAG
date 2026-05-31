import networkx as nx
from utils.loaders import load_metadata, load_graph, save_graph
from config import GRAPH_MAX_HOPS


class GraphService:
    def __init__(self):
        self.graph = self._load_or_build()

    def _load_or_build(self):
        g = load_graph()
        return g if g is not None else self._build_graph()

    def _build_graph(self):
        metadata = load_metadata()
        g = nx.Graph()

        # Create episode nodes
        for idx, entry in enumerate(metadata):
            ep_id = entry.get("episode_id") or entry.get("doc_id")
            g.add_node(
                ep_id,
                node_type="episode",
                chunk_index=idx,
                char_count=entry.get("char_count", 0),
                token_count=entry.get("token_count", 0),
            )

        # Create character nodes and edges
        for entry in metadata:
            ep_id = entry.get("episode_id") or entry.get("doc_id")
            characters = entry.get("characters", [])

            for char in characters:
                if not g.has_node(char):
                    g.add_node(char, node_type="character")

                # APPEARS_IN edge
                if g.has_edge(char, ep_id):
                    g[char][ep_id]["weight"] += 1
                else:
                    g.add_edge(char, ep_id, edge_type="APPEARS_IN", weight=1)

            # SPEAKS_TO edges
            for i, c1 in enumerate(characters):
                for c2 in characters[i + 1:]:
                    if g.has_edge(c1, c2):
                        g[c1][c2]["weight"] += 1
                    else:
                        g.add_edge(c1, c2, edge_type="SPEAKS_TO", weight=1)

        save_graph(g)
        return g

    def expand_context(self, chunk_indices, metadata):
        expanded = set()
        ep_to_idx = {}
        
        for idx, entry in enumerate(metadata):
            ep_id = entry.get("episode_id") or entry.get("doc_id")
            if ep_id not in ep_to_idx:
                ep_to_idx[ep_id] = []
            ep_to_idx[ep_id].append(idx)

        for idx in chunk_indices:
            if idx >= len(metadata):
                continue
            start = metadata[idx].get("episode_id") or metadata[idx].get("doc_id")
            if start not in self.graph:
                continue

            visited = set()
            frontier = {start}
            
            for _ in range(GRAPH_MAX_HOPS):
                next_frontier = set()
                for node in frontier:
                    if node in visited:
                        continue
                    visited.add(node)
                    
                    for neighbor in self.graph.neighbors(node):
                        if neighbor not in visited:
                            next_frontier.add(neighbor)
                            if self.graph.nodes[neighbor].get("node_type") == "episode":
                                expanded.update(ep_to_idx.get(neighbor, []))
                
                frontier = next_frontier

        return list(expanded - set(chunk_indices))

    def get_character_episodes(self, character_name):
        if character_name not in self.graph:
            return []
        
        return [
            n for n in self.graph.neighbors(character_name)
            if self.graph.nodes[n].get("node_type") == "episode"
        ]

    def filter_character_indices(self, character_name, metadata, name_variants=None):
        names = [character_name] + (name_variants or [])
        episodes = set()
        
        for name in names:
            episodes.update(self.get_character_episodes(name))

        return [
            idx for idx, entry in enumerate(metadata)
            if (entry.get("episode_id") or entry.get("doc_id")) in episodes
        ]


graph_service = GraphService()
