"""
Unit tests for GraphStore class
"""

import json

import pytest
from graph_store import GraphStore
from models import Entity, EntityType, Relationship, RelationType


class TestGraphStore:
    """Test suite for GraphStore class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.graph_store = GraphStore()

    def test_add_entity(self, sample_entities):
        """Test adding entities to graph store"""
        entity = sample_entities[0]  # Python entity
        self.graph_store.add_entity(entity)

        assert len(self.graph_store.entities) == 1
        assert entity.id in self.graph_store.entities
        assert self.graph_store.graph.has_node(entity.id)
        assert "chunk1" in self.graph_store.chunk_entities
        assert "chunk2" in self.graph_store.chunk_entities
        assert entity.id in self.graph_store.chunk_entities["chunk1"]
        assert entity.id in self.graph_store.chunk_entities["chunk2"]

    def test_add_multiple_entities(self, sample_entities):
        """Test adding multiple entities"""
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        assert len(self.graph_store.entities) == len(sample_entities)
        assert all(entity.id in self.graph_store.entities for entity in sample_entities)
        assert all(
            self.graph_store.graph.has_node(entity.id) for entity in sample_entities
        )

    def test_add_relationship(self, sample_entities, sample_relationship):
        """Test adding relationships to graph store"""
        # Add entities first
        self.graph_store.add_entity(sample_entities[0])  # Python
        self.graph_store.add_entity(sample_entities[1])  # Flask

        # Add relationship
        self.graph_store.add_relationship(sample_relationship)

        assert self.graph_store.graph.has_edge(
            sample_relationship.source_entity_id, sample_relationship.target_entity_id
        )

        edge_data = self.graph_store.graph.get_edge_data(
            sample_relationship.source_entity_id, sample_relationship.target_entity_id
        )
        assert len(edge_data) > 0

    def test_add_relationship_missing_entity(self, sample_relationship):
        """Test adding relationship when entities don't exist"""
        with pytest.raises(ValueError, match="Both entities must exist"):
            self.graph_store.add_relationship(sample_relationship)

    def test_get_entity(self, sample_entities):
        """Test retrieving entities by ID"""
        entity = sample_entities[0]
        self.graph_store.add_entity(entity)

        retrieved = self.graph_store.get_entity(entity.id)
        assert retrieved is not None
        assert retrieved.id == entity.id
        assert retrieved.name == entity.name

        # Test non-existent entity
        non_existent = self.graph_store.get_entity("non_existent_id")
        assert non_existent is None

    def test_get_entities_by_type(self, sample_entities):
        """Test retrieving entities by type"""
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        tech_entities = self.graph_store.get_entities_by_type(EntityType.TECHNOLOGY)
        course_entities = self.graph_store.get_entities_by_type(EntityType.COURSE)

        assert len(tech_entities) == 2  # Python and Flask
        assert len(course_entities) == 1  # Web Development

        tech_names = [e.name for e in tech_entities]
        assert "Python" in tech_names
        assert "Flask" in tech_names

    def test_get_entities_in_chunk(self, sample_entities):
        """Test retrieving entities for a specific chunk"""
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        entities_chunk1 = self.graph_store.get_entities_in_chunk("chunk1")
        entities_chunk2 = self.graph_store.get_entities_in_chunk("chunk2")
        entities_chunk3 = self.graph_store.get_entities_in_chunk("chunk3")

        assert len(entities_chunk1) == 3  # All entities appear in chunk1
        assert len(entities_chunk2) == 1  # Only Python appears in chunk2
        assert len(entities_chunk3) == 0  # No entities in chunk3

    def test_get_related_entities(self, sample_entities, sample_relationship):
        """Test finding related entities"""
        # Add entities and relationship
        for entity in sample_entities[:2]:  # Python and Flask only
            self.graph_store.add_entity(entity)
        self.graph_store.add_relationship(sample_relationship)

        # Test forward relationship
        related_to_python = self.graph_store.get_related_entities(
            "tech_python", max_depth=1
        )
        assert "tech_flask" in related_to_python

        # Test backward relationship
        related_to_flask = self.graph_store.get_related_entities(
            "tech_flask", max_depth=1
        )
        assert "tech_python" in related_to_flask

    def test_get_related_entities_with_filter(self, sample_entities):
        """Test finding related entities with relationship type filter"""
        # Add entities
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        # Add different types of relationships
        uses_rel = Relationship(
            source_entity_id="tech_python",
            target_entity_id="tech_flask",
            relation_type=RelationType.USES,
            chunk_ids={"chunk1"},
        )
        teaches_rel = Relationship(
            source_entity_id="course_webdev",
            target_entity_id="tech_python",
            relation_type=RelationType.TEACHES,
            chunk_ids={"chunk1"},
        )

        self.graph_store.add_relationship(uses_rel)
        self.graph_store.add_relationship(teaches_rel)

        # Filter by USES relationship
        uses_related = self.graph_store.get_related_entities(
            "tech_python", relation_types=[RelationType.USES], max_depth=1
        )
        assert "tech_flask" in uses_related
        assert "course_webdev" not in uses_related  # This is a TEACHES relationship

    def test_get_related_entities_max_depth(self, sample_entities):
        """Test max_depth parameter in related entities search"""
        # Create a chain: A -> B -> C
        entityA = Entity(
            id="a", name="A", entity_type=EntityType.CONCEPT, chunk_ids={"chunk1"}
        )
        entityB = Entity(
            id="b", name="B", entity_type=EntityType.CONCEPT, chunk_ids={"chunk1"}
        )
        entityC = Entity(
            id="c", name="C", entity_type=EntityType.CONCEPT, chunk_ids={"chunk1"}
        )

        for entity in [entityA, entityB, entityC]:
            self.graph_store.add_entity(entity)

        rel_ab = Relationship(
            source_entity_id="a",
            target_entity_id="b",
            relation_type=RelationType.RELATES_TO,
            chunk_ids={"chunk1"},
        )
        rel_bc = Relationship(
            source_entity_id="b",
            target_entity_id="c",
            relation_type=RelationType.RELATES_TO,
            chunk_ids={"chunk1"},
        )

        self.graph_store.add_relationship(rel_ab)
        self.graph_store.add_relationship(rel_bc)

        # Test depth 1: should only find B
        related_depth1 = self.graph_store.get_related_entities("a", max_depth=1)
        assert "b" in related_depth1
        assert "c" not in related_depth1

        # Test depth 2: should find both B and C
        related_depth2 = self.graph_store.get_related_entities("a", max_depth=2)
        assert "b" in related_depth2
        assert "c" in related_depth2

    def test_get_chunks_for_entities(self, sample_entities):
        """Test retrieving chunks for given entities"""
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        entity_ids = {"tech_python", "tech_flask"}
        chunks = self.graph_store.get_chunks_for_entities(entity_ids)

        assert "chunk1" in chunks  # Both entities appear in chunk1
        assert "chunk2" in chunks  # Python appears in chunk2
        assert len(chunks) == 2

    def test_find_shortest_path(self, sample_entities, sample_relationship):
        """Test shortest path finding between entities"""
        # Add entities and relationship
        for entity in sample_entities[:2]:
            self.graph_store.add_entity(entity)
        self.graph_store.add_relationship(sample_relationship)

        # Test path exists
        path = self.graph_store.find_shortest_path("tech_python", "tech_flask")
        assert path is not None
        assert len(path) == 2
        assert path[0] == "tech_python"
        assert path[1] == "tech_flask"

        # Test no path exists
        unconnected_entity = Entity(
            id="unconnected",
            name="Unconnected",
            entity_type=EntityType.CONCEPT,
            chunk_ids={"chunk3"},
        )
        self.graph_store.add_entity(unconnected_entity)

        no_path = self.graph_store.find_shortest_path("tech_python", "unconnected")
        assert no_path is None

    def test_get_entity_centrality(self, sample_entities):
        """Test centrality measures calculation"""
        # Add entities
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        # Add relationships to create a connected graph
        relationships = [
            Relationship(
                source_entity_id="tech_python",
                target_entity_id="tech_flask",
                relation_type=RelationType.USES,
                chunk_ids={"chunk1"},
            ),
            Relationship(
                source_entity_id="course_webdev",
                target_entity_id="tech_python",
                relation_type=RelationType.TEACHES,
                chunk_ids={"chunk1"},
            ),
            Relationship(
                source_entity_id="course_webdev",
                target_entity_id="tech_flask",
                relation_type=RelationType.TEACHES,
                chunk_ids={"chunk1"},
            ),
        ]

        for rel in relationships:
            self.graph_store.add_relationship(rel)

        # Test different centrality measures
        degree_centrality = self.graph_store.get_entity_centrality("degree")
        assert isinstance(degree_centrality, dict)
        assert len(degree_centrality) == 3
        assert all(0 <= score <= 1 for score in degree_centrality.values())

        try:
            pagerank_centrality = self.graph_store.get_entity_centrality("pagerank")
            assert isinstance(pagerank_centrality, dict)
            assert len(pagerank_centrality) == 3
        except (ImportError, ModuleNotFoundError):
            # Skip pagerank test if scipy is not available
            pytest.skip("scipy not available for pagerank calculation")

        # Test invalid measure
        with pytest.raises(ValueError, match="Unknown centrality measure"):
            self.graph_store.get_entity_centrality("invalid")

    def test_serialization_round_trip(self, sample_entities, sample_relationship):
        """Test serialization and deserialization"""
        # Add data to graph
        for entity in sample_entities[:2]:
            self.graph_store.add_entity(entity)
        self.graph_store.add_relationship(sample_relationship)

        # Serialize
        json_data = self.graph_store.serialize_to_json()
        assert isinstance(json_data, str)
        assert len(json_data) > 0

        # Verify JSON is valid
        parsed_data = json.loads(json_data)
        assert "entities" in parsed_data
        assert "relationships" in parsed_data
        assert "chunk_entities" in parsed_data

        # Deserialize into new graph
        new_graph = GraphStore()
        new_graph.load_from_json(json_data)

        # Verify preservation
        assert len(new_graph.entities) == len(self.graph_store.entities)
        assert (
            new_graph.graph.number_of_edges()
            == self.graph_store.graph.number_of_edges()
        )
        assert "tech_python" in new_graph.entities
        assert "tech_flask" in new_graph.entities
        assert new_graph.graph.has_edge("tech_python", "tech_flask")

    def test_serialization_empty_graph(self):
        """Test serialization of empty graph"""
        json_data = self.graph_store.serialize_to_json()
        parsed_data = json.loads(json_data)

        assert parsed_data["entities"] == {}
        assert parsed_data["relationships"] == []
        assert parsed_data["chunk_entities"] == {}

        # Test loading empty data
        new_graph = GraphStore()
        new_graph.load_from_json(json_data)
        assert len(new_graph.entities) == 0
        assert new_graph.graph.number_of_edges() == 0

    def test_load_invalid_json(self):
        """Test loading invalid JSON data"""
        with pytest.raises(ValueError, match="Failed to load graph data"):
            self.graph_store.load_from_json("invalid json")

        # Test with valid JSON but missing required fields
        with pytest.raises(ValueError, match="Failed to load graph data"):
            self.graph_store.load_from_json(
                '{"entities": {"test": {"missing_required_fields": true}}}'
            )

    def test_get_statistics(self, sample_entities, sample_relationship):
        """Test graph statistics calculation"""
        # Empty graph
        empty_stats = self.graph_store.get_statistics()
        assert empty_stats["total_entities"] == 0
        assert empty_stats["total_relationships"] == 0
        assert empty_stats["total_chunks_with_entities"] == 0

        # Add data
        for entity in sample_entities[:2]:
            self.graph_store.add_entity(entity)
        self.graph_store.add_relationship(sample_relationship)

        stats = self.graph_store.get_statistics()
        assert stats["total_entities"] == 2
        assert stats["total_relationships"] == 1
        assert stats["total_chunks_with_entities"] == 2  # chunk1 and chunk2
        assert stats["connected_components"] == 1

    def test_clear(self, sample_entities):
        """Test clearing graph data"""
        # Add some data
        for entity in sample_entities:
            self.graph_store.add_entity(entity)

        assert len(self.graph_store.entities) > 0
        assert len(self.graph_store.chunk_entities) > 0

        # Clear and verify
        self.graph_store.clear()

        assert len(self.graph_store.entities) == 0
        assert len(self.graph_store.chunk_entities) == 0
        assert self.graph_store.graph.number_of_nodes() == 0
        assert self.graph_store.graph.number_of_edges() == 0
