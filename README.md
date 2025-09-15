# EduConnect Chatbot - Architecture Documentation

## Overview

EduConnect is a hybrid retrieval-augmented generation (RAG) chatbot designed for educational guidance. It combines structured knowledge from a Neo4j graph database with semantic search capabilities to provide comprehensive answers about universities, programs, and admission processes.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Server (main.py)                      │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐ │
│  │   /chat         │  │   /mode          │  │   /health /clear-cache  │ │
│  │   Endpoints     │  │   Control        │  │   Utility Endpoints     │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    HybridRAGChain (ragchain.py)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐           ┌─────────────────┐                     │
│  │   Graph Mode    │    OR     │   Hybrid Mode   │                     │
│  │                 │           │                 │                     │
│  │ ┌─────────────┐ │           │ ┌─────────────┐ │                     │
│  │ │Graph Query  │ │           │ │Graph Query  │ │                     │
│  │ │     +       │ │           │ │     +       │ │                     │
│  │ │LLM Synthesis│ │           │ │Semantic     │ │                     │
│  │ └─────────────┘ │           │ │Retrieval    │ │                     │
│  └─────────────────┘           │ │     +       │ │                     │
│                                 │ │LLM Synthesis│ │                     │
│                                 │ └─────────────┘ │                     │
│                                 └─────────────────┘                     │
└─────────┬─────────────────────────────┬─────────────────────────────────┘
          │                             │
          ▼                             ▼
┌─────────────────────┐         ┌─────────────────────┐
│  GraphCypherQAChain │         │   Neo4jVector       │
│  (LangChain)        │         │   Retriever         │
│                     │         │                     │
│  ┌───────────────┐  │         │  ┌───────────────┐  │
│  │Cypher         │  │         │  │Vector         │  │
│  │Generation     │  │         │  │Similarity     │  │
│  │(via LLM)      │  │         │  │Search         │  │
│  └───────────────┘  │         │  └───────────────┘  │
└─────────┬───────────┘         └─────────┬───────────┘
          │                               │
          ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Neo4j Graph Database                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐              ┌─────────────────────┐           │
│  │   Knowledge Graph   │              │   Vector Index      │           │
│  │                     │              │                     │           │
│  │ ┌─────────────────┐ │              │ ┌─────────────────┐ │           │
│  │ │University       │ │              │ │Embeddings       │ │           │
│  │ │Program          │ │              │ │(University      │ │           │
│  │ │Requirements     │ │              │ │ text properties)│ │           │
│  │ │Test             │ │              │ └─────────────────┘ │           │
│  │ │Scholarship      │ │              └─────────────────────┘           │
│  │ │Location         │ │                                                │
│  │ │Tier/FeeRange    │ │                                                │
│  │ │AcceptanceCategor│ │                                                │
│  │ └─────────────────┘ │                                                │
│  └─────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    External Services                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐              ┌─────────────────────┐           │
│  │   Google Gemini     │              │   Neo4j Aura        │           │
│  │   (LLM Provider)    │              │   (Cloud Database)  │           │
│  │                     │              │                     │           │
│  │ • Cypher Generation │              │ • Graph Storage     │           │
│  │ • Answer Synthesis  │              │ • Vector Storage    │           │
│  │ • Text Processing   │              │ • Query Processing  │           │
│  └─────────────────────┘              └─────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Server (main.py)

The main application server providing RESTful APIs for client interaction.

**Key Features:**
- Singleton pattern for service initialization
- LRU caching for performance optimization
- Mode switching capabilities (graph-only vs hybrid)
- Thread-safe initialization

**API Endpoints:**
- `POST /chat` - Main conversation endpoint
- `GET/POST /mode` - Mode control (graph-only/hybrid toggle)
- `GET /health` - Service health check
- `POST /clear-cache` - Cache management

### 2. HybridRAGChain (ragchain.py)

The core orchestration layer that manages two operational modes:

**Graph-Only Mode:**
```
User Query → Cypher Generation → Neo4j Query → Graph Results → LLM Synthesis → Response
```

**Hybrid Mode:**
```
User Query → ┌─ Cypher Generation → Neo4j Query → Graph Results ─┐
             │                                                  ├─ LLM Synthesis → Response
             └─ Vector Search → Semantic Results ──────────────┘
```

**Key Components:**
- `GraphCypherQAChain` - Handles structured graph queries
- `Neo4jVector` retriever - Manages semantic search
- LLM synthesis prompt - Combines and formats results
- Mode detection and routing logic

### 3. GraphService (graph_service.py)

Manages the Neo4j database connection and data population.

**Responsibilities:**
- Neo4j graph connection management
- University data ingestion and relationship creation
- Vector store initialization for semantic search
- Graph schema enrichment (tiers, fee ranges, acceptance categories)

**Data Model:**
```
University ──┬─[LOCATED_IN]──→ Location
             ├─[OFFERS]──→ Program
             ├─[HAS_REQUIREMENTS]──→ Requirements
             ├─[REQUIRES_TEST]──→ Test
             ├─[OFFERS_SCHOLARSHIP]──→ Scholarship
             ├─[BELONGS_TO_TIER]──→ Tier
             ├─[HAS_FEE_RANGE]──→ FeeRange
             └─[HAS_ACCEPTANCE_RATE]──→ AcceptanceCategory
```

### 4. Configuration Management (config.py)

Environment-based configuration system:

- `Neo4jConfig` - Database connection settings
- `GeminiConfig` - LLM provider configuration
- `DATA_LOCATION` - Data file paths

## Operational Modes

### Graph-Only Mode (Fast)

**Purpose:** Optimized for speed when structured data is sufficient.

**Process Flow:**
1. Convert natural language to Cypher query
2. Execute query against Neo4j graph
3. Process results through LLM for formatting
4. Skip semantic retrieval entirely

**Performance:** ~40-60% faster response times
**Use Case:** Factual queries about universities, rankings, requirements

### Hybrid Mode (Comprehensive)

**Purpose:** Maximum coverage combining structured and unstructured data.

**Process Flow:**
1. Execute graph query (same as graph-only)
2. Perform vector similarity search
3. Combine both result sets
4. Synthesize comprehensive answer via LLM

**Performance:** Slower but more comprehensive
**Use Case:** Complex questions requiring contextual understanding

## Data Architecture

### Graph Schema

The Neo4j database contains structured educational data organized around universities:

**Core Entities:**
- **University**: Central entity with properties (name, location, rank, tuition, acceptance_rate)
- **Program**: Academic programs offered
- **Requirements**: Admission requirements (GPA, tests)
- **Location**: Geographic information
- **Tier**: Ranking classifications (Top 10, Top 25, etc.)
- **FeeRange**: Tuition cost categories
- **AcceptanceCategory**: Selectivity classifications

**Derived Relationships:**
- Geographic clustering (same state)
- Program sharing between universities
- Tier-based groupings
- Fee range classifications

### Vector Index

Semantic search capability built on university text properties:
- University names and descriptions
- Location information
- Website content
- Ranking details
- Tuition information

## Caching Strategy

**Multi-level Caching:**
1. **Request-level caching**: Complete responses cached by question + mode
2. **Component-level caching**: Graph service initialization cached
3. **LRU eviction**: Automatic cache management with configurable size limits

**Cache Keys:**
- Format: `{question}::{mode}` 
- Ensures mode-specific caching
- Prevents cross-contamination between graph-only and hybrid results

## Performance Characteristics

**Graph-Only Mode:**
- Latency: 200-800ms typical
- Throughput: Higher due to reduced I/O
- Accuracy: High for structured queries
- Coverage: Limited to graph data

**Hybrid Mode:**
- Latency: 800-2000ms typical
- Throughput: Moderate due to dual retrieval
- Accuracy: Very high with context augmentation
- Coverage: Comprehensive across all data types

## Error Handling and Resilience

**Graceful Degradation:**
- Semantic retrieval failure → Fall back to graph-only results
- Graph query failure → Return LLM knowledge-based response
- Vector store unavailable → Continue with graph data only

**Error Recovery:**
- Automatic retry logic for transient failures
- Circuit breaker pattern for external service calls
- Comprehensive logging for debugging

## Security Considerations

**Database Access:**
- Read-only database user recommended for production
- Connection string encryption
- Query validation and sanitization

**API Security:**
- Input validation and sanitization
- Rate limiting capabilities
- Error message sanitization to prevent information leakage

## Scalability Design

**Horizontal Scaling:**
- Stateless service design enables load balancing
- Shared cache strategy for multi-instance deployment
- Database connection pooling

**Vertical Scaling:**
- LRU cache size tuning
- Vector index optimization
- Query result pagination support

## Monitoring and Observability

**Performance Metrics:**
- Response time distribution by mode
- Cache hit/miss ratios
- Database query performance
- LLM inference latency

**Business Metrics:**
- Query success rates
- Mode usage distribution
- User engagement patterns
- Error frequency and types
