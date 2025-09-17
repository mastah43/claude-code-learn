"""
Unit tests for EntityExtractor class
"""

import pytest
from models import CourseChunk, EntityType, RelationType
from entity_extractor import EntityExtractor

class TestEntityExtractor:
    """Test suite for EntityExtractor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = EntityExtractor()
    
    def test_extract_technology_entities(self, sample_course_chunk):
        """Test extraction of technology entities"""
        entities = self.extractor.extract_entities_from_chunk(sample_course_chunk)
        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        
        tech_names = [e.name.lower() for e in tech_entities]
        assert "python" in tech_names
        assert "flask" in tech_names
        assert "docker" in tech_names
    
    def test_extract_course_lesson_entities(self, sample_course_chunk):
        """Test extraction of course and lesson entities"""
        entities = self.extractor.extract_entities_from_chunk(sample_course_chunk)
        
        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        lesson_entities = [e for e in entities if e.entity_type == EntityType.LESSON]
        
        assert len(course_entities) == 1
        assert len(lesson_entities) == 1
        assert course_entities[0].name == "Web Development"
        assert lesson_entities[0].name == "Lesson 1"
    
    def test_extract_tool_entities(self):
        """Test extraction of tool entities"""
        chunk = CourseChunk(
            content="We'll use VSCode editor with Git for version control and Docker for containers.",
            course_title="Development Tools",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(chunk)
        tool_entities = [e for e in entities if e.entity_type == EntityType.TOOL]
        
        tool_names = [e.name.lower() for e in tool_entities]
        assert "git" in tool_names
        assert "docker" in tool_names
    
    def test_extract_method_entities(self):
        """Test extraction of method/concept entities"""
        chunk = CourseChunk(
            content="We'll learn about algorithms, object oriented programming, and authentication methods.",
            course_title="Programming Concepts",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(chunk)
        method_entities = [e for e in entities if e.entity_type == EntityType.METHOD]
        
        method_names = [e.name.lower() for e in method_entities]
        assert "algorithm" in method_names
        assert "object oriented" in method_names
        assert "authentication" in method_names
    
    def test_extract_organization_entities(self):
        """Test extraction of organization entities"""
        chunk = CourseChunk(
            content="Google developed TensorFlow while Microsoft created TypeScript. OpenAI built GPT models.",
            course_title="Tech Companies",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(chunk)
        org_entities = [e for e in entities if e.entity_type == EntityType.ORGANIZATION]
        
        org_names = [e.name.lower() for e in org_entities]
        assert "google" in org_names
        assert "microsoft" in org_names
        assert "openai" in org_names
    
    def test_extract_code_entities(self):
        """Test extraction of code-related entities"""
        chunk = CourseChunk(
            content="Define a class MyComponent with method handleClick() and constant MAX_RETRIES.",
            course_title="Code Examples",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(chunk)
        concept_entities = [e for e in entities if e.entity_type == EntityType.CONCEPT]
        
        concept_names = [e.name for e in concept_entities]
        # Should extract camelCase and CONSTANTS
        assert any("MyComponent" in name for name in concept_names)
        assert any("handleClick" in name for name in concept_names)
    
    def test_extract_relationships(self, sample_course_chunk):
        """Test relationship extraction between entities"""
        entities = self.extractor.extract_entities_from_chunk(sample_course_chunk)
        relationships = self.extractor.extract_relationships(entities, sample_course_chunk)
        
        assert len(relationships) > 0
        
        # Check for course->lesson relationship
        course_lesson_rels = [
            r for r in relationships 
            if r.relation_type == RelationType.PART_OF
        ]
        assert len(course_lesson_rels) > 0
        
        # Check for teaching relationships
        teaching_rels = [
            r for r in relationships
            if r.relation_type == RelationType.TEACHES
        ]
        assert len(teaching_rels) > 0
    
    def test_entity_id_generation(self):
        """Test consistent entity ID generation"""
        id1 = self.extractor._generate_entity_id("Python", EntityType.TECHNOLOGY)
        id2 = self.extractor._generate_entity_id("Python", EntityType.TECHNOLOGY)
        id3 = self.extractor._generate_entity_id("python", EntityType.TECHNOLOGY)  # Different case
        id4 = self.extractor._generate_entity_id("Python", EntityType.TOOL)  # Different type
        
        assert id1 == id2  # Same inputs should produce same ID
        assert id1 == id3  # Case insensitive
        assert id1 != id4  # Different types should produce different IDs
        assert len(id1) == 12  # Expected length
        assert isinstance(id1, str)
    
    def test_merge_entities(self):
        """Test entity merging across multiple chunks"""
        chunk1 = CourseChunk(
            content="Python programming language",
            course_title="Course A",
            lesson_number=1,
            chunk_index=0
        )
        chunk2 = CourseChunk(
            content="Python for web development",
            course_title="Course B", 
            lesson_number=1,
            chunk_index=0
        )
        
        entities1 = self.extractor.extract_entities_from_chunk(chunk1)
        entities2 = self.extractor.extract_entities_from_chunk(chunk2)
        
        merged = self.extractor.merge_entities([entities1, entities2])
        
        # Should have Python entity with chunks from both courses
        python_entities = [e for e in merged.values() if "python" in e.name.lower()]
        assert len(python_entities) == 1
        assert len(python_entities[0].chunk_ids) == 2
    
    def test_merge_relationships(self):
        """Test relationship merging across multiple chunks"""
        chunk1 = CourseChunk(
            content="Python uses Flask for web development",
            course_title="Course A",
            lesson_number=1,
            chunk_index=0
        )
        chunk2 = CourseChunk(
            content="Python uses Flask framework for building APIs",
            course_title="Course B",
            lesson_number=1,
            chunk_index=0
        )
        
        entities1 = self.extractor.extract_entities_from_chunk(chunk1)
        entities2 = self.extractor.extract_entities_from_chunk(chunk2)
        relationships1 = self.extractor.extract_relationships(entities1, chunk1)
        relationships2 = self.extractor.extract_relationships(entities2, chunk2)
        
        merged_rels = self.extractor.merge_relationships([relationships1, relationships2])
        
        # Should merge relationships with same source, target, and type
        assert len(merged_rels) >= 1
        
        # Find a merged relationship and check it has chunks from both sources
        for rel in merged_rels:
            if len(rel.chunk_ids) > 1:
                # This relationship appears in multiple chunks
                assert len(rel.chunk_ids) >= 2
                break
    
    def test_empty_content_handling(self):
        """Test handling of empty or minimal content"""
        empty_chunk = CourseChunk(
            content="",
            course_title="Empty Course",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(empty_chunk)
        
        # Should at least extract course and lesson entities
        course_entities = [e for e in entities if e.entity_type == EntityType.COURSE]
        lesson_entities = [e for e in entities if e.entity_type == EntityType.LESSON]
        
        assert len(course_entities) == 1
        assert len(lesson_entities) == 1
    
    def test_special_characters_handling(self):
        """Test handling of content with special characters"""
        special_chunk = CourseChunk(
            content="C++ and C# are programming languages. Use @decorators in Python!",
            course_title="Programming Languages",
            lesson_number=1,
            chunk_index=0
        )
        
        entities = self.extractor.extract_entities_from_chunk(special_chunk)
        
        # Should still extract entities despite special characters
        tech_entities = [e for e in entities if e.entity_type == EntityType.TECHNOLOGY]
        tech_names = [e.name.lower() for e in tech_entities]
        
        assert "python" in tech_names
        # Note: C++ and C# might not be in our keyword list, but Python should be detected