"""
Pytest configuration and shared fixtures
"""

import os
import sys

import pytest

# Add the backend directory to the path so tests can import modules
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
sys.path.insert(0, backend_path)

from models import CourseChunk, Entity, EntityType, Relationship, RelationType


@pytest.fixture
def sample_course_chunk():
    """Fixture providing a sample course chunk for testing"""
    return CourseChunk(
        content="Python is a programming language used with Flask framework and Docker containers.",
        course_title="Web Development",
        lesson_number=1,
        chunk_index=0,
    )


@pytest.fixture
def sample_entities():
    """Fixture providing sample entities for testing"""
    return [
        Entity(
            id="tech_python",
            name="Python",
            entity_type=EntityType.TECHNOLOGY,
            chunk_ids={"chunk1", "chunk2"},
        ),
        Entity(
            id="tech_flask",
            name="Flask",
            entity_type=EntityType.TECHNOLOGY,
            chunk_ids={"chunk1"},
        ),
        Entity(
            id="course_webdev",
            name="Web Development",
            entity_type=EntityType.COURSE,
            chunk_ids={"chunk1"},
        ),
    ]


@pytest.fixture
def sample_relationship():
    """Fixture providing a sample relationship for testing"""
    return Relationship(
        source_entity_id="tech_python",
        target_entity_id="tech_flask",
        relation_type=RelationType.USES,
        chunk_ids={"chunk1"},
    )


@pytest.fixture
def ai_course_chunks():
    """Fixture providing AI-related course chunks for testing"""
    return [
        CourseChunk(
            content="Python is used for machine learning with TensorFlow.",
            course_title="AI Course",
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="TensorFlow enables deep learning and neural networks.",
            course_title="AI Course",
            lesson_number=2,
            chunk_index=1,
        ),
        CourseChunk(
            content="Machine learning algorithms require large datasets for training.",
            course_title="AI Course",
            lesson_number=3,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def frontend_course_chunks():
    """Fixture providing frontend development course chunks"""
    return [
        CourseChunk(
            content="React is a JavaScript library for building user interfaces with components.",
            course_title="Frontend Development",
            lesson_number=1,
            chunk_index=0,
        ),
        CourseChunk(
            content="JavaScript ES6 features include arrow functions and destructuring.",
            course_title="Frontend Development",
            lesson_number=2,
            chunk_index=1,
        ),
        CourseChunk(
            content="Node.js allows JavaScript to run on servers with Express framework.",
            course_title="Backend Development",
            lesson_number=1,
            chunk_index=0,
        ),
    ]
