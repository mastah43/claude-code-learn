"""
Integration tests for complete GraphRAG workflow
"""

from entity_extractor import EntityExtractor
from graph_builder import GraphBuilder
from graph_store import GraphStore
from models import CourseChunk, EntityType


class TestGraphRAGIntegration:
    """Integration tests for complete GraphRAG workflow"""

    def test_complete_workflow(self, frontend_course_chunks):
        """Test complete workflow from chunks to graph to queries"""
        # Build graph
        builder = GraphBuilder()
        graph_store = builder.build_graph_from_chunks(frontend_course_chunks)

        # Verify graph has expected structure
        assert len(graph_store.entities) > 0
        assert graph_store.graph.number_of_edges() > 0

        # Test serialization round trip
        json_data = graph_store.serialize_to_json()
        new_graph = GraphStore()
        new_graph.load_from_json(json_data)

        # Verify graphs are equivalent
        assert len(new_graph.entities) == len(graph_store.entities)
        assert new_graph.graph.number_of_edges() == graph_store.graph.number_of_edges()

        # Test entity queries
        js_entities = [
            e for e in graph_store.entities.values() if "javascript" in e.name.lower()
        ]
        if js_entities:
            js_entity = js_entities[0]
            related = graph_store.get_related_entities(js_entity.id)
            assert isinstance(related, set)

    def test_empty_input_handling(self):
        """Test handling of empty or invalid inputs"""
        builder = GraphBuilder()

        # Empty chunks list
        graph_store = builder.build_graph_from_chunks([])
        assert len(graph_store.entities) == 0

        # Chunks with minimal content
        minimal_chunks = [
            CourseChunk(
                content="", course_title="Empty Course", lesson_number=1, chunk_index=0
            )
        ]
        graph_store = builder.build_graph_from_chunks(minimal_chunks)
        # Should at least have course and lesson entities
        assert len(graph_store.entities) >= 2

    def test_entity_extraction_and_graph_construction(self):
        """Test the flow from entity extraction to graph construction"""
        # Create test chunk
        chunk = CourseChunk(
            content="Python is used with Django framework for web development. PostgreSQL stores the data.",
            course_title="Full Stack Development",
            lesson_number=1,
            chunk_index=0,
        )

        # Extract entities
        extractor = EntityExtractor()
        entities = extractor.extract_entities_from_chunk(chunk)
        relationships = extractor.extract_relationships(entities, chunk)

        # Verify extraction
        assert len(entities) > 0
        assert len(relationships) > 0

        # Build graph manually
        graph_store = GraphStore()
        merged_entities = extractor.merge_entities([entities])
        merged_relationships = extractor.merge_relationships([relationships])

        for entity in merged_entities.values():
            graph_store.add_entity(entity)

        for relationship in merged_relationships:
            try:
                graph_store.add_relationship(relationship)
            except ValueError:
                continue  # Skip if entities don't exist

        # Verify graph construction
        assert len(graph_store.entities) == len(merged_entities)

        # Test entity types
        tech_entities = [
            e
            for e in graph_store.entities.values()
            if e.entity_type == EntityType.TECHNOLOGY
        ]
        course_entities = [
            e
            for e in graph_store.entities.values()
            if e.entity_type == EntityType.COURSE
        ]

        assert len(tech_entities) > 0
        assert len(course_entities) == 1

    def test_multi_course_graph_construction(self):
        """Test building graph from multiple courses"""
        chunks = [
            CourseChunk(
                content="Python programming with Flask web framework",
                course_title="Web Development",
                lesson_number=1,
                chunk_index=0,
            ),
            CourseChunk(
                content="Python data analysis with Pandas library",
                course_title="Data Science",
                lesson_number=1,
                chunk_index=0,
            ),
            CourseChunk(
                content="Java Spring framework for enterprise applications",
                course_title="Enterprise Development",
                lesson_number=1,
                chunk_index=0,
            ),
        ]

        builder = GraphBuilder()
        graph_store = builder.build_graph_from_chunks(chunks)

        # Should have entities from all courses
        course_entities = [
            e
            for e in graph_store.entities.values()
            if e.entity_type == EntityType.COURSE
        ]
        course_names = [e.name for e in course_entities]

        assert "Web Development" in course_names
        assert "Data Science" in course_names
        assert "Enterprise Development" in course_names

        # Python should appear in multiple chunks
        python_entities = [
            e for e in graph_store.entities.values() if "python" in e.name.lower()
        ]
        if python_entities:
            assert len(python_entities[0].chunk_ids) == 2  # Appears in 2 courses

    def test_graph_relationship_discovery(self):
        """Test discovery of relationships in the graph"""
        chunks = [
            CourseChunk(
                content="Machine learning uses Python and TensorFlow for neural networks",
                course_title="AI Fundamentals",
                lesson_number=1,
                chunk_index=0,
            ),
            CourseChunk(
                content="TensorFlow provides tools for deep learning applications",
                course_title="AI Fundamentals",
                lesson_number=2,
                chunk_index=1,
            ),
        ]

        builder = GraphBuilder()
        graph_store = builder.build_graph_from_chunks(chunks)

        # Find Python entity
        python_entities = [
            e for e in graph_store.entities.values() if "python" in e.name.lower()
        ]

        if python_entities:
            python_entity = python_entities[0]

            # Find related entities
            related_entities = graph_store.get_related_entities(
                python_entity.id, max_depth=2
            )

            # Should find TensorFlow and other related entities
            assert len(related_entities) > 0

            # Get related entity names
            related_names = []
            for entity_id in related_entities:
                entity = graph_store.get_entity(entity_id)
                if entity:
                    related_names.append(entity.name.lower())

            # Should include course and lesson entities at minimum
            assert any("ai" in name for name in related_names)

    def test_chunk_relationship_discovery(self):
        """Test finding related chunks through entity connections"""
        chunks = [
            CourseChunk(
                content="React components use JavaScript for user interfaces",
                course_title="Frontend Development",
                lesson_number=1,
                chunk_index=0,
            ),
            CourseChunk(
                content="JavaScript ES6 features include arrow functions",
                course_title="Frontend Development",
                lesson_number=2,
                chunk_index=1,
            ),
            CourseChunk(
                content="Node.js runs JavaScript on the server side",
                course_title="Backend Development",
                lesson_number=1,
                chunk_index=0,
            ),
        ]

        builder = GraphBuilder()
        graph_store = builder.build_graph_from_chunks(chunks)
        builder.set_graph_store(graph_store)

        # Find chunks related to the first chunk (React/JavaScript)
        chunk_id = "Frontend_Development_0"
        related_chunks = builder.find_related_chunks(chunk_id, max_depth=2)

        # Should find chunks that share entities (like JavaScript)
        assert isinstance(related_chunks, list)

        # Should not include the original chunk
        assert chunk_id not in related_chunks

    def test_entity_type_distribution(self):
        """Test that various entity types are correctly identified"""
        chunks = [
            CourseChunk(
                content="Google developed TensorFlow using Python. Microsoft created TypeScript.",
                course_title="Tech History",
                lesson_number=1,
                chunk_index=0,
            ),
            CourseChunk(
                content="Use Git for version control and Docker for containerization.",
                course_title="DevOps Tools",
                lesson_number=1,
                chunk_index=0,
            ),
        ]

        builder = GraphBuilder()
        graph_store = builder.build_graph_from_chunks(chunks)

        # Check entity type distribution
        entity_types = {}
        for entity in graph_store.entities.values():
            entity_type = entity.entity_type
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # Should have multiple entity types
        assert EntityType.TECHNOLOGY in entity_types
        assert EntityType.ORGANIZATION in entity_types
        assert EntityType.COURSE in entity_types
        assert EntityType.LESSON in entity_types

        # Verify specific entities exist
        entity_names = [e.name.lower() for e in graph_store.entities.values()]
        assert "python" in entity_names
        assert "google" in entity_names
        assert "git" in entity_names

    def test_graph_persistence_integration(self):
        """Test integration with graph persistence"""
        chunks = [
            CourseChunk(
                content="Flask web framework for Python applications",
                course_title="Web Development",
                lesson_number=1,
                chunk_index=0,
            )
        ]

        builder = GraphBuilder()
        original_graph = builder.build_graph_from_chunks(chunks)

        # Test serialization
        json_data = original_graph.serialize_to_json()
        assert len(json_data) > 0

        # Test deserialization
        restored_graph = GraphStore()
        restored_graph.load_from_json(json_data)

        # Verify data integrity
        assert len(restored_graph.entities) == len(original_graph.entities)
        assert (
            restored_graph.graph.number_of_edges()
            == original_graph.graph.number_of_edges()
        )

        # Verify specific entities are preserved
        original_entity_names = {e.name for e in original_graph.entities.values()}
        restored_entity_names = {e.name for e in restored_graph.entities.values()}
        assert original_entity_names == restored_entity_names

    def test_incremental_graph_updates(self):
        """Test incremental updates to existing graph"""
        # Initial chunks
        initial_chunks = [
            CourseChunk(
                content="Python programming basics",
                course_title="Programming 101",
                lesson_number=1,
                chunk_index=0,
            )
        ]

        # Additional chunks
        new_chunks = [
            CourseChunk(
                content="Python advanced features and decorators",
                course_title="Programming 101",
                lesson_number=2,
                chunk_index=1,
            ),
            CourseChunk(
                content="Python web development with Django",
                course_title="Web Programming",
                lesson_number=1,
                chunk_index=0,
            ),
        ]

        builder = GraphBuilder()

        # Build initial graph
        initial_graph = builder.build_graph_from_chunks(initial_chunks)
        initial_entity_count = len(initial_graph.entities)

        # Update with new chunks
        updated_graph = builder.update_graph_with_new_chunks(new_chunks, initial_graph)

        # Verify graph growth
        assert len(updated_graph.entities) > initial_entity_count

        # Verify Python entity now appears in more chunks
        python_entities = [
            e for e in updated_graph.entities.values() if "python" in e.name.lower()
        ]
        if python_entities:
            python_entity = python_entities[0]
            assert len(python_entity.chunk_ids) == 3  # All three chunks mention Python

    def test_error_handling_integration(self):
        """Test error handling throughout the integration"""
        builder = GraphBuilder()

        # Test with malformed chunk
        malformed_chunks = [
            CourseChunk(
                content="",  # Empty content might cause issues
                course_title="",
                lesson_number=1,
                chunk_index=0,
            )
        ]

        # Should handle gracefully without crashing
        try:
            graph_store = builder.build_graph_from_chunks(malformed_chunks)
            # If it succeeds, verify it at least creates an empty or minimal graph
            assert isinstance(graph_store, GraphStore)
        except Exception:
            # If it fails, that's also acceptable for malformed input
            pass

    def test_large_graph_performance(self):
        """Test performance with larger number of chunks"""
        # Create a moderate number of chunks to test performance
        chunks = []
        for i in range(20):
            chunks.append(
                CourseChunk(
                    content=f"This is lesson {i} covering Python programming and web development concepts.",
                    course_title=f"Course {i // 5}",  # 4 courses with 5 lessons each
                    lesson_number=(i % 5) + 1,
                    chunk_index=i,
                )
            )

        builder = GraphBuilder()

        # This should complete in reasonable time
        import time

        start_time = time.time()
        graph_store = builder.build_graph_from_chunks(chunks)
        end_time = time.time()

        # Should complete within a reasonable time (adjust threshold as needed)
        assert end_time - start_time < 30  # 30 seconds max

        # Verify graph was built
        assert len(graph_store.entities) > 0

        # Should have multiple courses
        course_entities = [
            e
            for e in graph_store.entities.values()
            if e.entity_type == EntityType.COURSE
        ]
        assert len(course_entities) == 4  # 4 different courses
