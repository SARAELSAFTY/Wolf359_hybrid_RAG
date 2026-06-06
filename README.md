# Wolf 359 RAG Chatbot

An advanced conversational AI system for exploring the Wolf 359 podcast universe through interactive dialogue. The chatbot features a **hybrid Retrieval-Augmented Generation (RAG)** architecture that combines semantic vector search with knowledge graph traversal to deliver contextually accurate responses.

## Key Features

### Dual-Mode Operation
- **Story Summarization Mode**: Get accurate, comprehensive answers about episodes, characters, plot developments, and themes
- **Character Role-Play Mode**: Chat directly with Doug Eiffel, the communications officer of the USS Hephaestus Station

### Advanced Retrieval System
- **Hybrid Search**: Combines FAISS vector similarity (semantic understanding) with NetworkX graph traversal (contextual relationships)
- **Smart Reranking**: Ensures the most relevant content is selected from across all 89 episodes
- **Knowledge Graph**: Maps character interactions, episode connections, and thematic relationships

### Intelligent LLM Selection
- **openai/gpt-oss-120b** for story mode: Fast, efficient summarization with sub-second latency
- **Llama-3.3-70B** for character mode: Superior personality consistency and conversational depth

### Privacy-Focused Design
- **Session-Only Memory**: Conversations exist only during active sessions
- **Automatic Cleanup**: All data deleted on logout
- **No Persistent Storage**: Nothing written to disk or databases

---

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Development](#development)
- [Contributing](#contributing)

---

## 🏗️ Architecture Overview

The system follows a clean layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (Streamlit)                     │
│  - Mode selector  - Chat interface  - Session management     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Core Business Logic                         │
│  graph_flow.py  →  Routes queries to appropriate engine      │
│  story_engine.py → Handles plot/character queries           │
│  character_engine.py → Doug Eiffel persona interactions      │
│  retrieval.py   →  Hybrid RAG orchestration                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Services Layer                           │
│  llm_service.py    → Groq API integration                    │
│  memory_service.py → Conversation state management           │
│  graph_service.py  → NetworkX operations                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data/Assets Layer                         │
│  embeddings.npy         → Pre-computed vector embeddings     │
│  vector_store.index     → FAISS similarity index             │
│  metadata.json          → Episode/speaker/scene metadata     │
│  relationship_graph.json → Serialized knowledge graph        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Interactive web interface |
| **Orchestration** | LangGraph | Agent workflow routing |
| **Vector Search** | FAISS | Semantic similarity retrieval |
| **Knowledge Graph** | NetworkX | Relationship mapping |
| **LLM Provider** | Groq API | Ultra-fast inference |
| **Memory** | LangChain | Conversation state |
| **Data Format** | JSON + NumPy | Metadata and embeddings |

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+**
- **Internet connection** for API access
- **Groq API key** ([Get one here](https://console.groq.com/))

### Step-by-Step Setup

1. **Clone the repository**

```bash
git clone https://github.com/SARAELSAFTY/Wolf359_hybrid_RAG.git

```

2. **Create and activate a virtual environment**

```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
STORY_MODEL=openai/gpt-oss-120b
CHARACTER_MODEL=llama-3.3-70b-versatile
MAX_MEMORY_EXCHANGES=10
VECTOR_TOP_K=20
FINAL_TOP_K=5
```

5. **Verify asset files**

Ensure these files exist in the `assets/` directory:
- `new_embeddings.npy`
- `faiss_v7.index`
- `newmetadata_v7.json`
- `relationship_graph_2.json`


---

## ⚙️ Configuration

### config.py

All configuration is centralized in `config.py`:

---

## 💻 Usage

### Running the Application

**Start the Streamlit interface:**

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### Story Mode

Ask factual questions about the Wolf 359 universe:

**Example queries:**
- "Summarize Episode 15"
- "Who is Commander Minkowski?"
- "What is the chronology of the Hephaestus Station crisis?"
- "What are the main themes of Wolf 359?"
- "How do Doug and Minkowski's relationship evolve?"

**Model Used:** openai/gpt-oss-120b  
**Focus:** Factual accuracy, comprehensive coverage  
**Memory:** None (each query is independent)

### Character Mode (Doug Eiffel)

Have a conversation with Doug Eiffel:

**Example queries:**
- "How's life on the station?"
- "What do you think about Commander Minkowski?"
- "Tell me about your podcast logs"
- "What do you miss most about Earth?"
- "How do you deal with Dr. Hilbert?"

**Model Used:** Llama-3.3-70B  
**Focus:** Character consistency, personality, conversational memory  
**Memory:** Last 10 exchanges maintained during session

---

## 📁 Project Structure

```
wolf359-rag/
│
├── app.py                      # Main Streamlit application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in version control)
├── README.md                   # This file
│
├── core/                       # Business logic layer
│   ├── __init__.py
│   ├── graph_flow.py          # LangGraph workflow routing
│   ├── retrieval.py           # Hybrid retrieval orchestration
│   ├── story_engine.py        # Story summarization handler
│   ├── character_engine.py    # Doug Eiffel persona handler
│   └── prompts.py             # Prompt templates and formatting
│
├── services/                   # Infrastructure services
│   ├── __init__.py
│   ├── llm_service.py         # Groq API wrapper with streaming
│   ├── memory_service.py      # LangChain memory management
│   └── graph_service.py       # NetworkX graph operations
│
├── ui/                         # Presentation layer
│   ├── __init__.py
│   └── streamlit_ui.py        # Reusable UI components
│
├── utils/                      # Shared utilities
│   ├── __init__.py
│   └── loaders.py             # Data loading utilities
│
└── assets/                     # Pre-computed data
    ├── new_embeddings.npy          # Chunk embeddings (NumPy array)
    ├── faiss_v7.index      # FAISS similarity index
    ├── newmetadata_v7.json           # Episode/speaker/scene metadata
    └── relationship_graph_2.json # Serialized NetworkX graph
```

### Key Files Explained

| File | Responsibility | Key Functions |
|------|----------------|---------------|
| `app.py` | Application entry point | `main()`, `init_session_state()` |
| `core/graph_flow.py` | Query routing logic | `QueryRouter`, `route_query()` |
| `core/retrieval.py` | Hybrid RAG pipeline | `HybridRetriever`, `retrieve()`, `rerank()` |
| `core/story_engine.py` | Story query processing | `StoryEngine`, `handle_query()` |
| `core/character_engine.py` | Character interactions | `CharacterEngine`, `handle_query()` |
| `services/llm_service.py` | LLM API interface | `GroqClient`, `generate()`, `stream_generate()` |
| `services/memory_service.py` | Conversation state | `MemoryManager`, `add_message()`, `get_history()` |
| `services/graph_service.py` | Graph operations | `GraphService`, `expand_context()` |

---

## 🔍 How It Works

### Query Processing Flow

When you submit a query, here's what happens:

#### 1. **Input Reception**
The Streamlit UI captures your query and current mode selection.

#### 2. **Workflow Routing**
`graph_flow.py` analyzes the query and routes it to the appropriate engine (Story or Character).

#### 3. **Hybrid Retrieval**

**Vector Search:**
- Query is embedded into a vector
- FAISS searches for the top-20 most semantically similar script chunks
- Uses cosine similarity for ranking

**Graph Expansion:**
- For each retrieved chunk, traverse the knowledge graph
- Explore up to 2 hops to find:
  - Related episodes
  - Character interactions
  - Thematic connections
- Follow edges: `CONTAINS`, `SPEAKS_TO`, `APPEARS_IN`

**Merging & Reranking:**
- Combine results with weighted scoring: `score = 0.6 × vector_sim + 0.4 × graph_proximity`
- Remove duplicates
- Apply diversity filter (spread across episodes)
- Select final top-5 chunks

#### 4. **Memory Retrieval** (Character mode only)
The system retrieves the last 10 conversation exchanges to maintain continuity.

#### 5. **Prompt Assembly**
The prompt combines:
- System instructions (role definition, behavioral guidelines)
- Retrieved context chunks (with episode/speaker attribution)
- Conversation history (Character mode only)
- Current query

#### 6. **LLM Generation**
- **Story Mode**: openai/gpt-oss-120b `temperature=0.3` for factual accuracy
- **Character Mode**: Llama-3.3-70B with `temperature=0.7` for personality

Response is streamed token-by-token for real-time display.

#### 7. **Memory Update** (Character mode only)
The exchange is added to memory, with the oldest dropped if exceeding 10 exchanges.

---

## 🛠️ Development

### Building Assets from Scratch

If you need to rebuild the pre-computed assets:

PDFs LINK : https://drive.google.com/drive/folders/15rK6Qbf8kHviHBCIdC_7WAVJX4fIvrqM

---

## 🙏 Acknowledgments

- **Wolf 359 Podcast**: Created by Gabriel Urbina
- **Groq**: For providing ultra-fast LLM inference
- **LangChain & LangGraph**: For orchestration frameworks
- **FAISS**: For efficient vector similarity search
- **NetworkX**: For knowledge graph operations
- **Streamlit**: For rapid UI development

---

## 🎯 Quick Start Summary

```bash
# 1. Clone and setup
git clone https://github.com/SARAELSAFTY/Wolf359_hybrid_RAG.git
cd wolf359-rag
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
streamlit run app.py
```

**That's it!** Open and start chatting with Doug Eiffel or exploring the Wolf 359 universe.

---

**Built with ❤️ for the Wolf 359 fan community**
