# GraphRAG Tests

This directory contains comprehensive unit and integration tests for the GraphRAG implementation.

## Test Structure

### Unit Tests
- `test_entity_extractor.py` - Tests for entity extraction and NLP processing
- `test_graph_store.py` - Tests for knowledge graph storage and operations  
- `test_graph_builder.py` - Tests for graph construction and management

### Integration Tests
- `test_integration.py` - End-to-end workflow tests and integration scenarios

### Configuration
- `conftest.py` - Shared fixtures and test configuration
- `__init__.py` - Package initialization

## Running Tests

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_entity_extractor.py
```

### Run Specific Test
```bash
pytest tests/test_entity_extractor.py::TestEntityExtractor::test_entity_id_generation
```

### Run with Coverage
```bash
pytest --cov=backend --cov-report=html
```

### Run Only Unit Tests
```bash
pytest -m unit
```

### Run Only Integration Tests  
```bash
pytest -m integration
```

## Test Categories

### Entity Extraction Tests (`test_entity_extractor.py`)
- Technology entity detection (Python, Flask, Docker, etc.)
- Tool entity detection (Git, VSCode, etc.)
- Method/concept entity detection (algorithms, patterns, etc.)
- Organization entity detection (Google, Microsoft, etc.)
- Code entity detection (camelCase, CONSTANTS)
- Relationship extraction between entities
- Entity ID generation and consistency
- Entity merging across multiple chunks

### Graph Store Tests (`test_graph_store.py`)
- Entity addition and retrieval
- Relationship management
- Graph traversal and querying
- Entity search by type and chunk
- Related entity discovery
- Shortest path finding
- Centrality measures calculation
- Graph serialization/deserialization
- Statistics and analytics

### Graph Builder Tests (`test_graph_builder.py`)
- Complete graph construction from chunks
- Incremental graph updates
- Related chunk discovery
- Entity connection analysis
- Graph summarization
- Performance with multiple chunks

### Integration Tests (`test_integration.py`)
- Complete workflow testing
- Multi-course graph construction
- Cross-entity relationship discovery
- Performance testing
- Error handling
- Persistence integration

## Test Fixtures

### Shared Fixtures (in `conftest.py`)
- `sample_course_chunk` - Basic course chunk for testing
- `sample_entities` - Pre-defined entities for testing
- `sample_relationship` - Sample entity relationship
- `ai_course_chunks` - AI/ML related course content
- `frontend_course_chunks` - Frontend development content

## Test Data

Tests use realistic course content covering:
- **Programming Languages**: Python, JavaScript, TypeScript
- **Frameworks**: Flask, React, Django, TensorFlow
- **Tools**: Git, Docker, VSCode, Node.js
- **Concepts**: Machine learning, web development, algorithms
- **Organizations**: Google, Microsoft, OpenAI

## Expected Test Results

### Entity Extraction
- Should identify 20+ entity types across technology, tools, methods, organizations
- Should create proper hierarchical relationships (course → lesson → concepts)
- Should merge duplicate entities across chunks

### Graph Construction  
- Should build connected graphs with 100+ entities for moderate datasets
- Should maintain referential integrity between entities and relationships
- Should enable multi-hop traversal for related content discovery

### Performance Benchmarks
- Entity extraction: < 1 second per chunk
- Graph construction: < 30 seconds for 100 chunks
- Graph queries: < 100ms for typical traversals
- Serialization: < 5 seconds for large graphs

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure backend path is in PYTHONPATH
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **NetworkX Warnings**: Normal for graph operations
4. **Pydantic Warnings**: Using latest model syntax

### Debug Options
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run specific markers
pytest -m "not slow"
```

## Contributing

When adding new tests:
1. Follow existing naming conventions (`test_*.py`)
2. Use descriptive test names (`test_extract_technology_entities`)
3. Include docstrings for test methods
4. Use appropriate fixtures from `conftest.py`
5. Add integration tests for new features
6. Ensure tests are independent and can run in any order