from typing import Dict, Any, Optional, List, Set
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults
from graph_store import GraphStore
from search_tools import Tool

class GraphEnhancedSearchTool(Tool):
    """Enhanced search tool that combines vector search with knowledge graph traversal"""
    
    def __init__(self, vector_store: VectorStore, graph_store: Optional[GraphStore] = None):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.last_sources = []
        self.graph_enhanced = graph_store is not None
    
    def set_graph_store(self, graph_store: GraphStore):
        """Set the graph store for enhanced search capabilities"""
        self.graph_store = graph_store
        self.graph_enhanced = True
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        description = "Search course materials with smart course name matching and lesson filtering"
        if self.graph_enhanced:
            description += ". Includes related content through knowledge graph connections."
        
        return {
            "name": "search_course_content",
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "What to search for in the course content"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                    },
                    "include_related": {
                        "type": "boolean",
                        "description": "Whether to include semantically related chunks via knowledge graph (default: true)"
                    },
                    "max_related_chunks": {
                        "type": "integer",
                        "description": "Maximum number of related chunks to include (default: 3)"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, 
                lesson_number: Optional[int] = None, include_related: bool = True,
                max_related_chunks: int = 3) -> str:
        """
        Execute the enhanced search with optional graph-based expansion.
        
        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter
            include_related: Whether to include graph-related chunks
            max_related_chunks: Maximum related chunks to include
            
        Returns:
            Formatted search results or error message
        """
        
        # First, perform traditional vector search
        primary_results = self.vector_store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # Handle errors from primary search
        if primary_results.error:
            return primary_results.error
        
        # If no graph store or not including related content, return traditional results
        if not self.graph_enhanced or not include_related or primary_results.is_empty():
            return self._format_traditional_results(primary_results, course_name, lesson_number)
        
        # Perform graph-enhanced search
        try:
            enhanced_results = self._perform_graph_enhanced_search(
                primary_results, max_related_chunks
            )
            return self._format_enhanced_results(enhanced_results, primary_results)
            
        except Exception as e:
            print(f"Graph enhancement failed, falling back to traditional search: {e}")
            return self._format_traditional_results(primary_results, course_name, lesson_number)
    
    def _perform_graph_enhanced_search(self, primary_results: SearchResults, 
                                     max_related_chunks: int) -> Dict[str, Any]:
        """Perform graph-enhanced search to find related chunks"""
        
        # Get chunk IDs from primary results
        primary_chunk_ids = []
        for meta in primary_results.metadata:
            course_title = meta.get('course_title', '').replace(' ', '_')
            chunk_index = meta.get('chunk_index', 0)
            chunk_id = f"{course_title}_{chunk_index}"
            primary_chunk_ids.append(chunk_id)
        
        # Find related chunks through the knowledge graph
        all_related_chunk_ids = set()
        for chunk_id in primary_chunk_ids:
            # Get entities in this chunk
            entities_in_chunk = self.graph_store.get_entities_in_chunk(chunk_id)
            
            # For each entity, find related entities
            for entity in entities_in_chunk:
                related_entity_ids = self.graph_store.get_related_entities(
                    entity.id, max_depth=2
                )
                
                # Get chunks containing these related entities
                related_chunks = self.graph_store.get_chunks_for_entities(related_entity_ids)
                all_related_chunk_ids.update(related_chunks)
        
        # Remove primary chunks from related chunks
        for chunk_id in primary_chunk_ids:
            all_related_chunk_ids.discard(chunk_id)
        
        # Limit the number of related chunks
        related_chunk_ids = list(all_related_chunk_ids)[:max_related_chunks]
        
        # Fetch the actual content for related chunks
        related_chunks_content = self._fetch_chunk_content(related_chunk_ids)
        
        return {
            'primary_results': primary_results,
            'related_chunks': related_chunks_content,
            'related_chunk_ids': related_chunk_ids
        }
    
    def _fetch_chunk_content(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch content for specific chunk IDs from the vector store"""
        chunks_content = []
        
        for chunk_id in chunk_ids:
            try:
                # Parse chunk ID to extract course and chunk index
                parts = chunk_id.rsplit('_', 1)
                if len(parts) != 2:
                    continue
                    
                course_title_encoded = parts[0]
                chunk_index = int(parts[1])
                
                # Reconstruct course title
                course_title = course_title_encoded.replace('_', ' ')
                
                # Search for this specific chunk
                results = self.vector_store.course_content.get(
                    ids=[chunk_id]
                )
                
                if results and 'documents' in results and results['documents']:
                    chunks_content.append({
                        'content': results['documents'][0],
                        'metadata': results['metadatas'][0] if results['metadatas'] else {},
                        'chunk_id': chunk_id
                    })
                    
            except (ValueError, IndexError, Exception) as e:
                print(f"Error fetching chunk {chunk_id}: {e}")
                continue
        
        return chunks_content
    
    def _format_traditional_results(self, results: SearchResults, 
                                  course_name: Optional[str], 
                                  lesson_number: Optional[int]) -> str:
        """Format traditional search results"""
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        formatted = []
        sources = []
        
        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            # Track source for the UI
            source = course_title
            if lesson_num is not None:
                source += f" - Lesson {lesson_num}"
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        self.last_sources = sources
        return "\n\n".join(formatted)
    
    def _format_enhanced_results(self, enhanced_results: Dict[str, Any], 
                               primary_results: SearchResults) -> str:
        """Format graph-enhanced search results"""
        formatted = []
        sources = []
        
        # Format primary results first
        for doc, meta in zip(primary_results.documents, primary_results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            header = f"[PRIMARY] [{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            source = f"{course_title}"
            if lesson_num is not None:
                source += f" - Lesson {lesson_num}"
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        # Format related chunks
        for chunk_data in enhanced_results['related_chunks']:
            content = chunk_data['content']
            meta = chunk_data['metadata']
            
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            header = f"[RELATED] [{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            source = f"{course_title} (related)"
            if lesson_num is not None:
                source += f" - Lesson {lesson_num}"
            sources.append(source)
            
            formatted.append(f"{header}\n{content}")
        
        self.last_sources = sources
        
        # Add summary of enhancement
        num_related = len(enhanced_results['related_chunks'])
        if num_related > 0:
            summary = f"\n\n[GraphRAG Enhanced] Found {num_related} related chunks through knowledge graph connections."
            formatted.append(summary)
        
        return "\n\n".join(formatted)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        if not self.graph_enhanced:
            return {"error": "No knowledge graph available"}
        
        return self.graph_store.get_statistics()
    
    def find_entity_connections(self, entity_name: str) -> Dict[str, Any]:
        """Find connections for a specific entity in the knowledge graph"""
        if not self.graph_enhanced:
            return {"error": "No knowledge graph available"}
        
        # Find entities matching the name
        matching_entities = []
        for entity in self.graph_store.entities.values():
            if entity_name.lower() in entity.name.lower():
                matching_entities.append(entity)
        
        if not matching_entities:
            return {"error": f"No entities found matching '{entity_name}'"}
        
        # Get connections for the first matching entity
        entity = matching_entities[0]
        related_entity_ids = self.graph_store.get_related_entities(entity.id, max_depth=1)
        
        connections = []
        for related_id in related_entity_ids:
            related_entity = self.graph_store.get_entity(related_id)
            if related_entity:
                connections.append({
                    'name': related_entity.name,
                    'type': related_entity.entity_type,
                    'chunks': len(related_entity.chunk_ids)
                })
        
        return {
            'entity': entity.name,
            'type': entity.entity_type,
            'chunks': len(entity.chunk_ids),
            'connections': connections[:10]  # Limit to top 10
        }