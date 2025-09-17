# GraphRAG Extension - Functional Specification

## Overview

This document specifies the functionality added to extend the existing RAG (Retrieval-Augmented Generation) system with GraphRAG capabilities to include semantically connected chunks in the model context.

## Core Features Added

### 1. Knowledge Graph Infrastructure

#### Graph Models (`models.py`)

- **Entity Model**: Represents entities in the knowledge graph
  - Types: CONCEPT, PERSON, TECHNOLOGY, TOOL, METHOD, ORGANIZATION, COURSE, LESSON
  - Tracks chunks where entity appears
  - Unique ID generation based on name and type

- **Relationship Model**: Represents connections between entities
  - Types: TEACHES, USES, IMPLEMENTS, PART_OF, RELATES_TO, PREREQUISITE, EXAMPLE_OF, MENTIONED_IN
  - Confidence scoring (0-1)
  - Source chunk tracking

- **GraphData Model**: Container for complete graph structure
  - Entity dictionary (ID -> Entity)
  - Relationship list
  - Chunk-entity mapping

#### Graph Storage (`graph_store.py`)

- **In-Memory Graph**: NetworkX-based directed multigraph
- **Entity Management**: Add, retrieve, query entities by type
- **Relationship Management**: Add and query entity relationships
- **Graph Traversal**: Multi-hop entity discovery with configurable depth
- **Centrality Analysis**: Degree, betweenness, closeness, PageRank measures
- **Serialization**: JSON export/import for persistence via ChromaDB

### 2. Entity Extraction & NLP Processing

#### Entity Extractor (`entity_extractor.py`)

- **Technology Entities**: Python, JavaScript, React, Docker, PostgreSQL, AI/ML frameworks
- **Tool Entities**: VSCode, Jupyter, Git, CLI tools, package managers
- **Method/Concept Entities**: Algorithms, design patterns, programming paradigms
- **Organization Entities**: Google, Microsoft, OpenAI, universities
- **Code Entities**: CamelCase identifiers, CONSTANTS from code blocks
- **Course/Lesson Entities**: Automatic extraction from chunk metadata

#### Relationship Detection

- **Hierarchical**: Course → Lesson relationships
- **Teaching**: Course/Lesson → Technology/Tool/Method relationships
- **Usage**: Technology → Tool relationships
- **Semantic**: Concept ↔ Technology/Tool/Method relationships
- **Confidence Scoring**: Based on extraction method and context

### 3. Enhanced Search & Retrieval

#### Graph-Enhanced Search Tool (`graph_search_tool.py`)

- **Hybrid Search**: Combines traditional vector search with graph traversal
- **Related Chunk Discovery**: Finds semantically connected chunks via entity relationships
- **Configurable Parameters**:
  - `include_related`: Enable/disable graph enhancement
  - `max_related_chunks`: Limit related content (default: 3)
  - `max_depth`: Graph traversal depth (default: 2)

#### Search Result Enhancement

- **Primary Results**: Traditional vector search results marked as `[PRIMARY]`
- **Related Results**: Graph-discovered chunks marked as `[RELATED]`
- **Source Tracking**: Enhanced source attribution including related content
- **Fallback Behavior**: Graceful degradation to traditional search on errors

### 4. RAG System Integration

#### Enhanced RAG System (`rag_system.py`)

- **Configuration**: `ENABLE_GRAPHRAG` flag for feature toggle
- **Graph Lifecycle**: Automatic graph construction during document ingestion
- **Persistence**: Graph data stored as JSON in ChromaDB metadata
- **Loading**: Automatic graph restoration on system startup
- **Analytics**: Extended course analytics with graph statistics

#### Graph Management API

- `rebuild_knowledge_graph()`: Rebuild entire graph from existing chunks
- `get_graph_summary()`: Entity type distribution and top central entities
- `find_entity_connections()`: Explore specific entity relationships

### 5. Data Persistence

#### Vector Store Extensions (`vector_store.py`)

- **Graph Collection**: New ChromaDB collection for graph data storage
- **JSON Storage**: Graph serialization in metadata fields
- **Data Integrity**: Coordinated clearing of vector and graph data

#### Serialization Format

```json
{
  "entities": {
    "entity_id": {
      "id": "string",
      "name": "string",
      "entity_type": "enum",
      "description": "string|null",
      "chunk_ids": ["array"]
    }
  },
  "relationships": [
    {
      "source_entity_id": "string",
      "target_entity_id": "string",
      "relation_type": "enum",
      "confidence": "float",
      "chunk_ids": ["array"]
    }
  ],
  "chunk_entities": {
    "chunk_id": ["entity_ids"]
  }
}
```

## Configuration Options

### Environment Variables

- `ENABLE_GRAPHRAG`: Enable GraphRAG features (default: True)
- `GRAPH_MAX_DEPTH`: Maximum graph traversal depth (default: 2)
- `GRAPH_MAX_RELATED`: Maximum related chunks to include (default: 3)

### Search Parameters

- `include_related`: Boolean to enable graph enhancement
- `max_related_chunks`: Integer limit for related content
- Traditional parameters: `query`, `course_name`, `lesson_number`

## Dependencies Added

### Required Packages

```
networkx>=3.0          # Graph operations and algorithms
spacy>=3.7.0          # Advanced NLP (optional enhancement)
```

### Existing Dependencies

- anthropic, chromadb, sentence-transformers (unchanged)
- pydantic, flask (unchanged)

## Performance Characteristics

### Memory Usage

- **Graph Storage**: O(E + V) where E=entities, V=relationships
- **In-Memory**: NetworkX provides efficient graph operations
- **Persistence**: JSON serialization for ChromaDB storage

### Query Performance

- **Entity Lookup**: O(1) hash table access
- **Graph Traversal**: O(V + E) for BFS within max_depth
- **Related Chunk Discovery**: O(k) where k=number of related entities

### Scalability

- **Linear Growth**: Entity extraction scales with chunk count
- **Efficient Indexing**: ChromaDB handles vector search, NetworkX handles graph queries
- **Configurable Limits**: Max depth and related chunks prevent exponential expansion

## Error Handling & Fallback

### Graceful Degradation

- Graph construction errors → traditional RAG continues
- Entity extraction failures → partial graph with available entities
- Graph query errors → fallback to vector search only
- Serialization issues → logged but non-blocking

### Logging & Monitoring

- Graph construction progress indicators
- Entity/relationship extraction statistics
- Error reporting with context preservation
- Performance metrics for graph operations

## Future Enhancement Opportunities

### Advanced NLP

- Named Entity Recognition with spaCy models
- Coreference resolution for entity linking
- Semantic role labeling for relationship extraction

### Graph Algorithms

- Community detection for topic clustering
- Graph embeddings for similarity computation
- Temporal graphs for course progression modeling

### User Interface

- Graph visualization for entity relationships
- Interactive exploration of knowledge connections
- Entity-centric search and browsing

## Testing & Validation

### Test Structure

- **Unit Tests**: Located in `/tests` directory following pytest conventions
  - `test_entity_extractor.py` - Entity extraction and NLP processing
  - `test_graph_store.py` - Knowledge graph storage and operations
  - `test_graph_builder.py` - Graph construction and management
- **Integration Tests**: `test_integration.py` - End-to-end workflow testing
- **Test Configuration**: `conftest.py` with shared fixtures and setup

### Test Coverage

- **Entity Extraction**: Technology, tool, method, organization, and code entity detection
- **Graph Operations**: Node/edge management, traversal, centrality analysis
- **Serialization**: JSON round-trip validation for persistence
- **Integration**: Complete workflow from chunks to enhanced search results
- **Performance**: Benchmarks for large datasets and graph operations

### Quality Metrics

- Entity extraction precision/recall across different content types
- Relationship accuracy assessment with confidence scoring
- Graph connectivity analysis and component detection
- Query response time benchmarks (< 100ms for typical traversals)
- Memory usage optimization for large knowledge graphs

### Test Execution

See the main [README.md](README.md#testing) for detailed test execution instructions and coverage information.
