from typing import List, Dict, Optional
from models import CourseChunk, Entity, Relationship, GraphData
from entity_extractor import EntityExtractor
from graph_store import GraphStore

class GraphBuilder:
    """Builds knowledge graphs from course content"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.graph_store = GraphStore()
    
    def build_graph_from_chunks(self, chunks: List[CourseChunk]) -> GraphStore:
        """Build a complete knowledge graph from course chunks"""
        print(f"Building knowledge graph from {len(chunks)} chunks...")
        
        # Extract entities and relationships from all chunks
        all_entities = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks):
            if i % 50 == 0:  # Progress indicator
                print(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Extract entities from this chunk
            chunk_entities = self.entity_extractor.extract_entities_from_chunk(chunk)
            all_entities.append(chunk_entities)
            
            # Extract relationships from this chunk
            chunk_relationships = self.entity_extractor.extract_relationships(chunk_entities, chunk)
            all_relationships.append(chunk_relationships)
        
        # Merge entities and relationships across all chunks
        print("Merging entities and relationships...")
        merged_entities = self.entity_extractor.merge_entities(all_entities)
        merged_relationships = self.entity_extractor.merge_relationships(all_relationships)
        
        # Add entities to graph store
        print(f"Adding {len(merged_entities)} entities to graph...")
        for entity in merged_entities.values():
            self.graph_store.add_entity(entity)
        
        # Add relationships to graph store
        print(f"Adding {len(merged_relationships)} relationships to graph...")
        for relationship in merged_relationships:
            try:
                self.graph_store.add_relationship(relationship)
            except ValueError as e:
                # Skip relationships where entities don't exist
                print(f"Skipping relationship: {e}")
                continue
        
        print("Knowledge graph construction complete!")
        print(f"Graph statistics: {self.graph_store.get_statistics()}")
        
        return self.graph_store
    
    def update_graph_with_new_chunks(self, new_chunks: List[CourseChunk], 
                                   existing_graph: GraphStore) -> GraphStore:
        """Update an existing graph with new chunks"""
        print(f"Updating graph with {len(new_chunks)} new chunks...")
        
        # Set the existing graph as our working graph
        self.graph_store = existing_graph
        
        # Process new chunks
        all_entities = []
        all_relationships = []
        
        for chunk in new_chunks:
            chunk_entities = self.entity_extractor.extract_entities_from_chunk(chunk)
            all_entities.append(chunk_entities)
            
            chunk_relationships = self.entity_extractor.extract_relationships(chunk_entities, chunk)
            all_relationships.append(chunk_relationships)
        
        # Merge new entities and relationships
        new_merged_entities = self.entity_extractor.merge_entities(all_entities)
        new_merged_relationships = self.entity_extractor.merge_relationships(all_relationships)
        
        # Add or update entities in the graph
        for entity in new_merged_entities.values():
            existing_entity = self.graph_store.get_entity(entity.id)
            if existing_entity:
                # Merge chunk_ids with existing entity
                existing_entity.chunk_ids.update(entity.chunk_ids)
                self.graph_store.add_entity(existing_entity)  # Update
            else:
                # Add new entity
                self.graph_store.add_entity(entity)
        
        # Add new relationships
        for relationship in new_merged_relationships:
            try:
                self.graph_store.add_relationship(relationship)
            except ValueError:
                continue
        
        print("Graph update complete!")
        print(f"Updated graph statistics: {self.graph_store.get_statistics()}")
        
        return self.graph_store
    
    def get_graph_summary(self) -> Dict:
        """Get a summary of the constructed graph"""
        stats = self.graph_store.get_statistics()
        
        # Get entity type distribution
        entity_types = {}
        for entity in self.graph_store.entities.values():
            entity_type = entity.entity_type
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Get most central entities
        try:
            centrality = self.graph_store.get_entity_centrality('pagerank')
            top_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_entity_names = []
            for entity_id, score in top_entities:
                entity = self.graph_store.get_entity(entity_id)
                if entity:
                    top_entity_names.append(f"{entity.name} ({entity.entity_type}, {score:.3f})")
        except:
            top_entity_names = []
        
        return {
            'basic_stats': stats,
            'entity_type_distribution': entity_types,
            'top_central_entities': top_entity_names
        }
    
    def find_related_chunks(self, query_chunk_id: str, max_depth: int = 2) -> List[str]:
        """Find chunks related to a given chunk through the knowledge graph"""
        # Get entities in the query chunk
        query_entities = self.graph_store.get_entities_in_chunk(query_chunk_id)
        if not query_entities:
            return []
        
        # Find related entities for each entity in the chunk
        related_entity_ids = set()
        for entity in query_entities:
            related_ids = self.graph_store.get_related_entities(
                entity.id, 
                max_depth=max_depth
            )
            related_entity_ids.update(related_ids)
        
        # Get chunks that contain these related entities
        related_chunk_ids = self.graph_store.get_chunks_for_entities(related_entity_ids)
        
        # Remove the original chunk from results
        related_chunk_ids.discard(query_chunk_id)
        
        return list(related_chunk_ids)
    
    def find_chunks_by_entity_name(self, entity_name: str, entity_type: Optional[str] = None) -> List[str]:
        """Find chunks that contain a specific entity"""
        # Find entities matching the name
        matching_entities = []
        for entity in self.graph_store.entities.values():
            if entity.name.lower() == entity_name.lower():
                if entity_type is None or entity.entity_type == entity_type:
                    matching_entities.append(entity)
        
        # Get all chunks for matching entities
        chunk_ids = set()
        for entity in matching_entities:
            chunk_ids.update(entity.chunk_ids)
        
        return list(chunk_ids)
    
    def get_entity_connections(self, entity_name: str) -> Dict:
        """Get detailed connection information for an entity"""
        # Find the entity
        target_entity = None
        for entity in self.graph_store.entities.values():
            if entity.name.lower() == entity_name.lower():
                target_entity = entity
                break
        
        if not target_entity:
            return {"error": f"Entity '{entity_name}' not found"}
        
        # Get related entities
        related_entity_ids = self.graph_store.get_related_entities(target_entity.id, max_depth=1)
        
        # Group related entities by type
        connections = {}
        for entity_id in related_entity_ids:
            related_entity = self.graph_store.get_entity(entity_id)
            if related_entity:
                entity_type = related_entity.entity_type
                if entity_type not in connections:
                    connections[entity_type] = []
                connections[entity_type].append(related_entity.name)
        
        return {
            'entity': target_entity.name,
            'type': target_entity.entity_type,
            'appears_in_chunks': len(target_entity.chunk_ids),
            'connections': connections
        }
    
    def clear_graph(self):
        """Clear the current graph"""
        self.graph_store.clear()
    
    def get_graph_store(self) -> GraphStore:
        """Get the current graph store instance"""
        return self.graph_store
    
    def set_graph_store(self, graph_store: GraphStore):
        """Set the graph store instance"""
        self.graph_store = graph_store