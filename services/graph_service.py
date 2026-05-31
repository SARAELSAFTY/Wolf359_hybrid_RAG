<<<<<<< HEAD
import json
import networkx as nx
from networkx.readwrite import json_graph

=======
import networkx as nx
>>>>>>> ed00e0d (Replace old files with new versions)
from utils.loaders import load_metadata, load_graph, save_graph
from config import GRAPH_MAX_HOPS


class GraphService:
<<<<<<< HEAD
    """
    Encapsulates all NetworkX graph operations.

    The knowledge graph links episodes and characters via edges
    representing interactions (SPEAKS_TO, APPEARS_IN). If no
    pre-built graph file exists, it is constructed from metadata.
    """

    def __init__(self):
        self.graph: nx.Graph = self._load_or_build()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------
    def _load_or_build(self) -> nx.Graph:
        """Load the serialised graph, or build it from metadata."""
        g = load_graph()
        if g is not None:
            return g
        return self._build_graph()

    def _build_graph(self) -> nx.Graph:
        """
        Build a knowledge graph from metadata.json.

        Creates nodes for each episode (doc_id) and each character
        (top_persons), and edges for APPEARS_IN and SPEAKS_TO.
        """
        metadata = load_metadata()
        g = nx.Graph()

        # --- Create episode nodes ---
        for idx, entry in enumerate(metadata):
            ep_id = entry["doc_id"]
=======
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
>>>>>>> ed00e0d (Replace old files with new versions)
            g.add_node(
                ep_id,
                node_type="episode",
                chunk_index=idx,
                char_count=entry.get("char_count", 0),
                token_count=entry.get("token_count", 0),
            )

<<<<<<< HEAD
        # --- Create character nodes and edges ---
        for entry in metadata:
            ep_id = entry["doc_id"]
            persons = entry.get("top_persons", [])

            for person in persons:
                # Add character node (idempotent)
                if not g.has_node(person):
                    g.add_node(person, node_type="character")

                # APPEARS_IN edge: character → episode
                if g.has_edge(person, ep_id):
                    g[person][ep_id]["weight"] = (
                        g[person][ep_id].get("weight", 1) + 1
                    )
                else:
                    g.add_edge(
                        person, ep_id, edge_type="APPEARS_IN", weight=1
                    )

            # SPEAKS_TO edges: character ↔ character within same episode
            for i, p1 in enumerate(persons):
                for p2 in persons[i + 1 :]:
                    if g.has_edge(p1, p2):
                        g[p1][p2]["weight"] = g[p1][p2].get("weight", 1) + 1
                    else:
                        g.add_edge(
                            p1, p2, edge_type="SPEAKS_TO", weight=1
                        )

        # Persist for next startup
        save_graph(g)
        return g

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def expand_context(self, chunk_indices: list[int], metadata: list[dict]) -> list[int]:
        """
        Given a list of chunk indices from vector search, expand context
        by traversing the knowledge graph up to GRAPH_MAX_HOPS hops.

        Returns a list of additional chunk indices discovered through
        graph neighbours (episodes sharing characters, etc.).
        """
        expanded_indices: set[int] = set()
        doc_id_to_indices = {}
        for idx, entry in enumerate(metadata):
            ep_id = entry["doc_id"]
            if ep_id not in doc_id_to_indices:
                doc_id_to_indices[ep_id] = []
            doc_id_to_indices[ep_id].append(idx)
=======
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
>>>>>>> ed00e0d (Replace old files with new versions)

        for idx in chunk_indices:
            if idx >= len(metadata):
                continue
<<<<<<< HEAD
            start_node = metadata[idx]["doc_id"]
            if start_node not in self.graph:
                continue

            # BFS up to GRAPH_MAX_HOPS
            visited = set()
            frontier = {start_node}
            for _hop in range(GRAPH_MAX_HOPS):
=======
            start = metadata[idx].get("episode_id") or metadata[idx].get("doc_id")
            if start not in self.graph:
                continue

            visited = set()
            frontier = {start}
            
            for _ in range(GRAPH_MAX_HOPS):
>>>>>>> ed00e0d (Replace old files with new versions)
                next_frontier = set()
                for node in frontier:
                    if node in visited:
                        continue
                    visited.add(node)
<<<<<<< HEAD
                    for neighbour in self.graph.neighbors(node):
                        if neighbour not in visited:
                            next_frontier.add(neighbour)
                            # If the neighbour is an episode node, record its index
                            if self.graph.nodes[neighbour].get("node_type") == "episode":
                                expanded_indices.update(doc_id_to_indices.get(neighbour, []))
                frontier = next_frontier

        # Remove the original indices — caller already has those
        return list(expanded_indices - set(chunk_indices))

    def find_connections(self, character_name: str) -> list[dict]:
        """
        Find all characters that interact with the given character,
        sorted by interaction weight (descending).
        """
        if character_name not in self.graph:
            return []

        connections = []
        for neighbour in self.graph.neighbors(character_name):
            edge_data = self.graph[character_name][neighbour]
            if edge_data.get("edge_type") == "SPEAKS_TO":
                connections.append(
                    {
                        "character": neighbour,
                        "weight": edge_data.get("weight", 1),
                    }
                )
        connections.sort(key=lambda c: c["weight"], reverse=True)
        return connections

    def get_character_episodes(self, character_name: str) -> list[str]:
        """Return all episode doc_ids in which a character appears."""
        if character_name not in self.graph:
            return []
        episodes = []
        for neighbour in self.graph.neighbors(character_name):
            if self.graph.nodes[neighbour].get("node_type") == "episode":
                episodes.append(neighbour)
        return episodes

    def filter_doug_indices(self, metadata: list[dict]) -> list[int]:
        """
        Return chunk indices for episodes where Doug Eiffel appears.
        Used in character mode to filter retrieval to Doug-relevant content.
        """
        doug_episodes = set()
        for name_variant in ["Doug", "Doug Eiffel", "Eiffel"]:
            doug_episodes.update(self.get_character_episodes(name_variant))

        return [
            idx
            for idx, entry in enumerate(metadata)
            if entry["doc_id"] in doug_episodes
        ]


# Module-level singleton
graph_service = GraphService()
=======
                    
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
>>>>>>> ed00e0d (Replace old files with new versions)
