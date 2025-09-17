import networkx as nx
import json
from typing import List, Dict, Set, Optional, Tuple
from models import Entity, Relationship, GraphData, EntityType, RelationType

class GraphStore:
    """In-memory knowledge graph using NetworkX with ChromaDB persistence"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Directed graph allowing multiple edges
        self.entities: Dict[str, Entity] = {}
        self.chunk_entities: Dict[str, Set[str]] = {}
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the graph"""
        self.entities[entity.id] = entity
        self.graph.add_node(entity.id, **entity.model_dump())
        
        # Update chunk-entity mapping
        for chunk_id in entity.chunk_ids:
            if chunk_id not in self.chunk_entities:
                self.chunk_entities[chunk_id] = set()
            self.chunk_entities[chunk_id].add(entity.id)
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph"""
        # Ensure both entities exist
        if (relationship.source_entity_id not in self.entities or 
            relationship.target_entity_id not in self.entities):
            raise ValueError(f"Both entities must exist before adding relationship")
        
        # Add edge with relationship data
        self.graph.add_edge(
            relationship.source_entity_id,
            relationship.target_entity_id,
            **relationship.model_dump()
        )
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type"""
        return [entity for entity in self.entities.values() 
                if entity.entity_type == entity_type]
    
    def get_entities_in_chunk(self, chunk_id: str) -> List[Entity]:
        """Get all entities mentioned in a specific chunk"""
        entity_ids = self.chunk_entities.get(chunk_id, set())
        return [self.entities[eid] for eid in entity_ids if eid in self.entities]
    
    def get_related_entities(self, entity_id: str, 
                           relation_types: Optional[List[RelationType]] = None,
                           max_depth: int = 1) -> Set[str]:
        """Get entities related to the given entity within max_depth hops"""
        if entity_id not in self.entities:
            return set()
        
        related = set()
        
        # Use BFS to find related entities within max_depth
        visited = set()
        queue = [(entity_id, 0)]  # (entity_id, depth)
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth >= max_depth:
                continue
                
            visited.add(current_id)
            
            # Get neighbors (both incoming and outgoing)
            neighbors = set(self.graph.successors(current_id)) | set(self.graph.predecessors(current_id))
            
            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    # Check relationship type filter if provided
                    if relation_types:
                        # Check if any edge between current and neighbor has desired relation type
                        edges = self.graph.get_edge_data(current_id, neighbor_id)
                        if not edges:
                            edges = self.graph.get_edge_data(neighbor_id, current_id)
                        
                        if edges and any(edge_data.get('relation_type') in relation_types 
                                       for edge_data in edges.values()):
                            related.add(neighbor_id)
                            if depth + 1 < max_depth:
                                queue.append((neighbor_id, depth + 1))
                    else:
                        related.add(neighbor_id)
                        if depth + 1 < max_depth:
                            queue.append((neighbor_id, depth + 1))
        
        return related
    
    def get_chunks_for_entities(self, entity_ids: Set[str]) -> Set[str]:
        """Get all chunk IDs that contain any of the given entities"""
        chunk_ids = set()
        for entity_id in entity_ids:
            if entity_id in self.entities:
                chunk_ids.update(self.entities[entity_id].chunk_ids)
        return chunk_ids
    
    def find_shortest_path(self, source_entity_id: str, target_entity_id: str) -> Optional[List[str]]:
        """Find shortest path between two entities"""
        try:
            return nx.shortest_path(self.graph.to_undirected(), source_entity_id, target_entity_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_entity_centrality(self, measure: str = 'degree') -> Dict[str, float]:
        """Calculate centrality measures for entities"""
        if measure == 'degree':
            return nx.degree_centrality(self.graph)
        elif measure == 'betweenness':
            return nx.betweenness_centrality(self.graph)
        elif measure == 'closeness':
            return nx.closeness_centrality(self.graph)
        elif measure == 'pagerank':
            return nx.pagerank(self.graph)
        else:
            raise ValueError(f"Unknown centrality measure: {measure}")
    
    def serialize_to_json(self) -> str:
        """Serialize graph data to JSON for ChromaDB storage"""
        relationships = []
        
        # Extract relationships from graph edges
        for source, target, edge_data in self.graph.edges(data=True):
            relationships.append({
                'source_entity_id': source,
                'target_entity_id': target,
                'relation_type': edge_data.get('relation_type'),
                'confidence': edge_data.get('confidence', 1.0),
                'chunk_ids': list(edge_data.get('chunk_ids', set()))
            })
        
        # Convert entities to serializable format
        entities_dict = {}
        for entity_id, entity in self.entities.items():
            entities_dict[entity_id] = {
                'id': entity.id,
                'name': entity.name,
                'entity_type': entity.entity_type,
                'description': entity.description,
                'chunk_ids': list(entity.chunk_ids)
            }
        
        graph_data = {
            'entities': entities_dict,
            'relationships': relationships,
            'chunk_entities': {k: list(v) for k, v in self.chunk_entities.items()}
        }
        
        return json.dumps(graph_data)
    
    def load_from_json(self, json_data: str) -> None:
        """Load graph data from JSON"""
        try:
            data = json.loads(json_data)
            
            # Clear existing data
            self.graph.clear()
            self.entities.clear()
            self.chunk_entities.clear()
            
            # Load entities
            for entity_data in data.get('entities', {}).values():
                entity = Entity(
                    id=entity_data['id'],
                    name=entity_data['name'],
                    entity_type=EntityType(entity_data['entity_type']),
                    description=entity_data.get('description'),
                    chunk_ids=set(entity_data.get('chunk_ids', []))
                )
                self.add_entity(entity)
            
            # Load relationships
            for rel_data in data.get('relationships', []):
                relationship = Relationship(
                    source_entity_id=rel_data['source_entity_id'],
                    target_entity_id=rel_data['target_entity_id'],
                    relation_type=RelationType(rel_data['relation_type']),
                    confidence=rel_data.get('confidence', 1.0),
                    chunk_ids=set(rel_data.get('chunk_ids', []))
                )
                self.add_relationship(relationship)
            
            # Load chunk-entity mapping
            chunk_entities_data = data.get('chunk_entities', {})
            self.chunk_entities = {k: set(v) for k, v in chunk_entities_data.items()}
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to load graph data from JSON: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get basic statistics about the graph"""
        return {
            'total_entities': len(self.entities),
            'total_relationships': self.graph.number_of_edges(),
            'total_chunks_with_entities': len(self.chunk_entities),
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }
    
    def clear(self) -> None:
        """Clear all graph data"""
        self.graph.clear()
        self.entities.clear()
        self.chunk_entities.clear()