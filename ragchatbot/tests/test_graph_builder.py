"""
Unit tests for GraphBuilder class
"""

import pytest
from models import CourseChunk, EntityType
from graph_builder import GraphBuilder
from graph_store import GraphStore

class TestGraphBuilder:
    """Test suite for GraphBuilder class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.builder = GraphBuilder()
    
    def test_build_graph_from_chunks(self, ai_course_chunks):
        """Test building complete graph from chunks"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        
        assert isinstance(graph_store, GraphStore)
        assert len(graph_store.entities) > 0
        assert graph_store.graph.number_of_edges() > 0
        
        # Should have course and lesson entities
        course_entities = [e for e in graph_store.entities.values() if e.entity_type == EntityType.COURSE]
        lesson_entities = [e for e in graph_store.entities.values() if e.entity_type == EntityType.LESSON]
        
        assert len(course_entities) >= 1
        assert len(lesson_entities) >= 3  # 3 lessons
        
        # Verify course name
        course_names = [e.name for e in course_entities]
        assert "AI Course" in course_names
    
    def test_build_graph_empty_chunks(self):
        """Test building graph from empty chunks list"""
        graph_store = self.builder.build_graph_from_chunks([])
        
        assert isinstance(graph_store, GraphStore)
        assert len(graph_store.entities) == 0
        assert graph_store.graph.number_of_edges() == 0
    
    def test_build_graph_minimal_content(self):
        """Test building graph from chunks with minimal content"""
        minimal_chunks = [
            CourseChunk(
                content="",
                course_title="Empty Course",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Short text.",
                course_title="Minimal Course",
                lesson_number=1,
                chunk_index=0
            )
        ]
        
        graph_store = self.builder.build_graph_from_chunks(minimal_chunks)
        
        # Should at least have course and lesson entities
        assert len(graph_store.entities) >= 4  # 2 courses + 2 lessons
        
        course_entities = [e for e in graph_store.entities.values() if e.entity_type == EntityType.COURSE]
        course_names = [e.name for e in course_entities]
        assert "Empty Course" in course_names
        assert "Minimal Course" in course_names
    
    def test_update_graph_with_new_chunks(self, ai_course_chunks):
        """Test updating existing graph with new chunks"""
        # Build initial graph with first chunk
        initial_graph = self.builder.build_graph_from_chunks(ai_course_chunks[:1])
        initial_entity_count = len(initial_graph.entities)
        initial_edge_count = initial_graph.graph.number_of_edges()
        
        # Add new chunks
        new_chunks = ai_course_chunks[1:]
        updated_graph = self.builder.update_graph_with_new_chunks(new_chunks, initial_graph)
        
        # Should have more entities and possibly more edges after update
        assert len(updated_graph.entities) >= initial_entity_count
        assert updated_graph.graph.number_of_edges() >= initial_edge_count
        
        # Verify it's the same graph object (updated in place)
        assert updated_graph is initial_graph
    
    def test_update_graph_with_overlapping_entities(self):
        """Test updating graph when new chunks contain existing entities"""
        # First chunk with Python
        chunk1 = [CourseChunk(
            content="Python programming language",
            course_title="Course A",
            lesson_number=1,
            chunk_index=0
        )]
        
        # Second chunk also with Python
        chunk2 = [CourseChunk(
            content="Python for data science",
            course_title="Course A",
            lesson_number=2,
            chunk_index=1
        )]
        
        # Build initial graph
        initial_graph = self.builder.build_graph_from_chunks(chunk1)
        
        # Find Python entity
        python_entities = [e for e in initial_graph.entities.values() 
                          if "python" in e.name.lower()]
        assert len(python_entities) == 1
        initial_chunk_count = len(python_entities[0].chunk_ids)
        
        # Update with new chunk
        updated_graph = self.builder.update_graph_with_new_chunks(chunk2, initial_graph)
        
        # Python entity should now appear in more chunks
        python_entities = [e for e in updated_graph.entities.values() 
                          if "python" in e.name.lower()]
        assert len(python_entities) == 1
        assert len(python_entities[0].chunk_ids) > initial_chunk_count
    
    def test_get_graph_summary(self, ai_course_chunks):
        """Test getting graph summary"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        summary = self.builder.get_graph_summary()
        
        assert isinstance(summary, dict)
        assert 'basic_stats' in summary
        assert 'entity_type_distribution' in summary
        assert 'top_central_entities' in summary
        
        # Verify basic stats
        basic_stats = summary['basic_stats']
        assert 'total_entities' in basic_stats
        assert 'total_relationships' in basic_stats
        assert basic_stats['total_entities'] > 0
        
        # Verify entity type distribution
        entity_dist = summary['entity_type_distribution']
        assert EntityType.COURSE in entity_dist or 'course' in entity_dist
        assert EntityType.LESSON in entity_dist or 'lesson' in entity_dist
    
    def test_find_related_chunks(self, ai_course_chunks):
        """Test finding related chunks through graph connections"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        self.builder.set_graph_store(graph_store)
        
        # Find chunks related to the first chunk
        chunk_id = "AI_Course_0"
        related_chunks = self.builder.find_related_chunks(chunk_id, max_depth=2)
        
        assert isinstance(related_chunks, list)
        # Should not include the original chunk
        assert chunk_id not in related_chunks
        
        # Test with non-existent chunk
        non_existent_related = self.builder.find_related_chunks("non_existent_chunk")
        assert non_existent_related == []
    
    def test_find_related_chunks_different_depths(self, frontend_course_chunks):
        """Test finding related chunks with different max depths"""
        graph_store = self.builder.build_graph_from_chunks(frontend_course_chunks)
        self.builder.set_graph_store(graph_store)
        
        chunk_id = "Frontend_Development_0"
        
        # Test depth 1
        related_depth1 = self.builder.find_related_chunks(chunk_id, max_depth=1)
        
        # Test depth 2
        related_depth2 = self.builder.find_related_chunks(chunk_id, max_depth=2)
        
        # Depth 2 should potentially find more or equal chunks
        assert len(related_depth2) >= len(related_depth1)
    
    def test_find_chunks_by_entity_name(self, ai_course_chunks):
        """Test finding chunks by entity name"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        self.builder.set_graph_store(graph_store)
        
        # Find chunks containing "Python"
        python_chunks = self.builder.find_chunks_by_entity_name("Python")
        assert isinstance(python_chunks, list)
        
        # Find chunks containing "TensorFlow"
        tensorflow_chunks = self.builder.find_chunks_by_entity_name("TensorFlow")
        assert isinstance(tensorflow_chunks, list)
        
        # Test case insensitive search
        python_chunks_lower = self.builder.find_chunks_by_entity_name("python")
        assert python_chunks_lower == python_chunks
        
        # Test non-existent entity
        non_existent_chunks = self.builder.find_chunks_by_entity_name("NonExistentEntity")
        assert non_existent_chunks == []
    
    def test_find_chunks_by_entity_name_with_type(self, ai_course_chunks):
        """Test finding chunks by entity name with type filter"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        self.builder.set_graph_store(graph_store)
        
        # Find chunks containing technology entities named "Python"
        tech_chunks = self.builder.find_chunks_by_entity_name("Python", EntityType.TECHNOLOGY)
        course_chunks = self.builder.find_chunks_by_entity_name("AI Course", EntityType.COURSE)
        
        assert isinstance(tech_chunks, list)
        assert isinstance(course_chunks, list)
        
        # Course chunks should be different from tech chunks for same name
        # (though they might overlap if entity names coincide)
    
    def test_get_entity_connections(self, ai_course_chunks):
        """Test getting entity connection information"""
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        self.builder.set_graph_store(graph_store)
        
        # Test with existing entity
        connections = self.builder.get_entity_connections("Python")
        
        if "error" not in connections:
            assert "entity" in connections
            assert "type" in connections
            assert "appears_in_chunks" in connections
            assert "connections" in connections
            assert connections["entity"] == "Python"
            assert isinstance(connections["appears_in_chunks"], int)
            assert isinstance(connections["connections"], dict)
        
        # Test with non-existent entity
        non_existent_connections = self.builder.get_entity_connections("NonExistentEntity")
        assert "error" in non_existent_connections
        assert "not found" in non_existent_connections["error"].lower()
    
    def test_clear_graph(self, ai_course_chunks):
        """Test clearing the graph"""
        # Build a graph
        graph_store = self.builder.build_graph_from_chunks(ai_course_chunks)
        assert len(graph_store.entities) > 0
        
        # Clear the graph
        self.builder.clear_graph()
        
        # Verify graph is empty
        current_graph = self.builder.get_graph_store()
        assert len(current_graph.entities) == 0
        assert current_graph.graph.number_of_edges() == 0
    
    def test_get_set_graph_store(self):
        """Test getting and setting graph store"""
        # Get initial graph store
        initial_store = self.builder.get_graph_store()
        assert isinstance(initial_store, GraphStore)
        
        # Create and set new graph store
        new_store = GraphStore()
        self.builder.set_graph_store(new_store)
        
        # Verify it was set
        retrieved_store = self.builder.get_graph_store()
        assert retrieved_store is new_store
        assert retrieved_store is not initial_store
    
    def test_concurrent_chunk_processing(self, frontend_course_chunks):
        """Test processing chunks with overlapping entities"""
        # All chunks mention JavaScript in different contexts
        js_chunks = [
            CourseChunk(
                content="JavaScript is a programming language for web development.",
                course_title="Web Basics",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="JavaScript frameworks like React make development easier.",
                course_title="Advanced Web",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Node.js runs JavaScript on the server side.",
                course_title="Backend Basics",
                lesson_number=1,
                chunk_index=0
            )
        ]
        
        graph_store = self.builder.build_graph_from_chunks(js_chunks)
        
        # Should have one JavaScript entity appearing in multiple chunks
        js_entities = [e for e in graph_store.entities.values() 
                      if "javascript" in e.name.lower()]
        assert len(js_entities) == 1
        assert len(js_entities[0].chunk_ids) == 3
        
        # Should have multiple courses
        course_entities = [e for e in graph_store.entities.values() 
                          if e.entity_type == EntityType.COURSE]
        assert len(course_entities) == 3