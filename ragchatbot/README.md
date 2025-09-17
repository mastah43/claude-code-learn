# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## GraphRAG Features

This system includes advanced GraphRAG (Graph Retrieval-Augmented Generation) capabilities that enhance traditional RAG with knowledge graph connections:

### Key Features
- **Entity Extraction**: Automatically identifies technologies, tools, methods, organizations, and concepts from course content
- **Knowledge Graph**: Builds semantic relationships between entities across courses and lessons
- **Enhanced Search**: Combines vector similarity with graph traversal to find semantically connected content
- **Multi-hop Reasoning**: Discovers related information through entity relationships
- **Persistent Storage**: Stores graph data alongside vector embeddings in ChromaDB

### Configuration
GraphRAG features can be configured via environment variables:
```bash
# Enable/disable GraphRAG (default: true)
ENABLE_GRAPHRAG=true

# Graph traversal depth (default: 2)
GRAPH_MAX_DEPTH=2

# Maximum related chunks to include (default: 3) 
GRAPH_MAX_RELATED=3
```

## Testing

The system includes comprehensive unit and integration tests for all GraphRAG functionality.

### Test Structure
- **Unit Tests**: Located in `/tests` directory following pytest conventions
  - `test_entity_extractor.py` - Entity extraction and NLP processing
  - `test_graph_store.py` - Knowledge graph storage and operations
  - `test_graph_builder.py` - Graph construction and management
- **Integration Tests**: `test_integration.py` - End-to-end workflow testing
- **Test Configuration**: `conftest.py` with shared fixtures and setup

### Running Tests

#### Install Test Dependencies
```bash
pip install -r requirements.txt
```

#### Run All Tests
```bash
pytest
```

#### Run Specific Test Categories
```bash
# Run entity extraction tests
pytest tests/test_entity_extractor.py

# Run graph storage tests  
pytest tests/test_graph_store.py

# Run integration tests
pytest tests/test_integration.py
```

#### Run with Coverage
```bash
pytest --cov=backend --cov-report=html
```

#### Run Specific Test Methods
```bash
# Run a specific test method
pytest tests/test_graph_store.py::TestGraphStore::test_add_entity

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Coverage
- **139+ individual test cases** covering all GraphRAG functionality
- **Entity extraction** for technologies, tools, methods, organizations
- **Graph operations** including traversal, centrality analysis, serialization
- **Integration workflows** from document ingestion to enhanced search
- **Performance benchmarks** for large datasets and graph operations
- **Error handling** and edge case validation

