from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict


class Lesson(BaseModel):
    """Represents a lesson within a course"""

    lesson_number: int  # Sequential lesson number (1, 2, 3, etc.)
    title: str  # Lesson title
    lesson_link: Optional[str] = None  # URL link to the lesson


class Course(BaseModel):
    """Represents a complete course with its lessons"""

    title: str  # Full course title (used as unique identifier)
    course_link: Optional[str] = None  # URL link to the course
    instructor: Optional[str] = None  # Course instructor name (optional metadata)
    lessons: List[Lesson] = []  # List of lessons in this course


class CourseChunk(BaseModel):
    """Represents a text chunk from a course for vector storage"""

    content: str  # The actual text content
    course_title: str  # Which course this chunk belongs to
    lesson_number: Optional[int] = None  # Which lesson this chunk is from
    chunk_index: int  # Position of this chunk in the document


# GraphRAG Models


class EntityType(str, Enum):
    """Types of entities in the knowledge graph"""

    CONCEPT = "concept"
    PERSON = "person"
    TECHNOLOGY = "technology"
    TOOL = "tool"
    METHOD = "method"
    ORGANIZATION = "organization"
    COURSE = "course"
    LESSON = "lesson"


class RelationType(str, Enum):
    """Types of relationships in the knowledge graph"""

    TEACHES = "teaches"
    USES = "uses"
    IMPLEMENTS = "implements"
    PART_OF = "part_of"
    RELATES_TO = "relates_to"
    PREREQUISITE = "prerequisite"
    EXAMPLE_OF = "example_of"
    MENTIONED_IN = "mentioned_in"


class Entity(BaseModel):
    """Represents an entity in the knowledge graph"""

    id: str  # Unique identifier
    name: str  # Entity name/label
    entity_type: EntityType  # Type of entity
    description: Optional[str] = None  # Optional description
    chunk_ids: Set[str] = set()  # Chunks where this entity appears

    model_config = ConfigDict(use_enum_values=True)


class Relationship(BaseModel):
    """Represents a relationship between entities"""

    source_entity_id: str  # Source entity ID
    target_entity_id: str  # Target entity ID
    relation_type: RelationType  # Type of relationship
    confidence: float = 1.0  # Confidence score (0-1)
    chunk_ids: Set[str] = set()  # Chunks supporting this relationship

    model_config = ConfigDict(use_enum_values=True)


class GraphData(BaseModel):
    """Container for complete graph data"""

    entities: Dict[str, Entity] = {}  # Entity ID -> Entity
    relationships: List[Relationship] = []  # List of all relationships
    chunk_entities: Dict[str, Set[str]] = {}  # Chunk ID -> Set of entity IDs
