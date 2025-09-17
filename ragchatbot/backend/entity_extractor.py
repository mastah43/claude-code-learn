import hashlib
import re
from collections import defaultdict
from typing import Dict, List

from models import CourseChunk, Entity, EntityType, Relationship, RelationType


class EntityExtractor:
    """Extract entities and relationships from course content using NLP techniques"""

    def __init__(self):
        # Technology-related keywords
        self.tech_keywords = {
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "rust",
            "go",
            "swift",
            "react",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
            "node.js",
            "express",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "git",
            "github",
            "gitlab",
            "jenkins",
            "terraform",
            "ansible",
            "api",
            "rest",
            "graphql",
            "ai",
            "ml",
            "machine learning",
            "artificial intelligence",
            "neural network",
            "llm",
            "rag",
            "retrieval augmented generation",
            "vector database",
            "embedding",
            "transformer",
        }

        # Tool-related keywords
        self.tool_keywords = {
            "vscode",
            "pycharm",
            "intellij",
            "eclipse",
            "vim",
            "emacs",
            "sublime text",
            "postman",
            "curl",
            "wget",
            "jupyter",
            "colab",
            "notebook",
            "terminal",
            "cli",
            "bash",
            "powershell",
            "ssh",
            "ftp",
            "sftp",
            "rsync",
            "wget",
            "pip",
            "npm",
            "yarn",
            "conda",
            "virtualenv",
            "pipenv",
            "poetry",
            "make",
            "cmake",
            "gradle",
            "maven",
        }

        # Method/concept keywords
        self.method_keywords = {
            "algorithm",
            "data structure",
            "sorting",
            "searching",
            "recursion",
            "iteration",
            "oop",
            "object oriented",
            "functional programming",
            "design pattern",
            "mvc",
            "microservices",
            "monolith",
            "crud",
            "authentication",
            "authorization",
            "encryption",
            "hashing",
            "caching",
            "optimization",
            "refactoring",
            "testing",
            "debugging",
            "deployment",
            "ci/cd",
            "devops",
            "agile",
            "scrum",
            "kanban",
            "tdd",
            "bdd",
        }

        # Organization keywords
        self.org_keywords = {
            "google",
            "microsoft",
            "amazon",
            "meta",
            "facebook",
            "apple",
            "netflix",
            "uber",
            "airbnb",
            "twitter",
            "linkedin",
            "github",
            "gitlab",
            "stackoverflow",
            "reddit",
            "openai",
            "anthropic",
            "deepmind",
            "nasa",
            "mit",
            "stanford",
            "berkeley",
            "cmu",
        }

        # Compile regex patterns for efficiency
        self.patterns = {
            "code_block": re.compile(r"```[\s\S]*?```|`[^`]+`"),
            "url": re.compile(r"https?://[^\s]+"),
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "camelcase": re.compile(r"\b[a-z]+[A-Z][a-zA-Z]*\b"),
            "capitals": re.compile(r"\b[A-Z]{2,}\b"),
        }

    def extract_entities_from_chunk(self, chunk: CourseChunk) -> List[Entity]:
        """Extract entities from a single course chunk"""
        entities = []
        content = chunk.content.lower()
        chunk_id = f"{chunk.course_title.replace(' ', '_')}_{chunk.chunk_index}"

        # Extract different types of entities
        entities.extend(self._extract_technology_entities(content, chunk_id))
        entities.extend(self._extract_tool_entities(content, chunk_id))
        entities.extend(self._extract_method_entities(content, chunk_id))
        entities.extend(self._extract_organization_entities(content, chunk_id))
        entities.extend(self._extract_course_lesson_entities(chunk, chunk_id))
        entities.extend(self._extract_code_entities(chunk.content, chunk_id))

        return entities

    def _extract_technology_entities(self, content: str, chunk_id: str) -> List[Entity]:
        """Extract technology-related entities"""
        entities = []
        for tech in self.tech_keywords:
            if tech in content:
                entity_id = self._generate_entity_id(tech, EntityType.TECHNOLOGY)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=tech.title(),
                        entity_type=EntityType.TECHNOLOGY,
                        chunk_ids={chunk_id},
                    )
                )
        return entities

    def _extract_tool_entities(self, content: str, chunk_id: str) -> List[Entity]:
        """Extract tool-related entities"""
        entities = []
        for tool in self.tool_keywords:
            if tool in content:
                entity_id = self._generate_entity_id(tool, EntityType.TOOL)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=tool.title(),
                        entity_type=EntityType.TOOL,
                        chunk_ids={chunk_id},
                    )
                )
        return entities

    def _extract_method_entities(self, content: str, chunk_id: str) -> List[Entity]:
        """Extract method/concept entities"""
        entities = []
        for method in self.method_keywords:
            if method in content:
                entity_id = self._generate_entity_id(method, EntityType.METHOD)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=method.title(),
                        entity_type=EntityType.METHOD,
                        chunk_ids={chunk_id},
                    )
                )
        return entities

    def _extract_organization_entities(
        self, content: str, chunk_id: str
    ) -> List[Entity]:
        """Extract organization entities"""
        entities = []
        for org in self.org_keywords:
            if org in content:
                entity_id = self._generate_entity_id(org, EntityType.ORGANIZATION)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=org.title(),
                        entity_type=EntityType.ORGANIZATION,
                        chunk_ids={chunk_id},
                    )
                )
        return entities

    def _extract_course_lesson_entities(
        self, chunk: CourseChunk, chunk_id: str
    ) -> List[Entity]:
        """Extract course and lesson entities"""
        entities = []

        # Course entity
        course_entity_id = self._generate_entity_id(
            chunk.course_title, EntityType.COURSE
        )
        entities.append(
            Entity(
                id=course_entity_id,
                name=chunk.course_title,
                entity_type=EntityType.COURSE,
                chunk_ids={chunk_id},
            )
        )

        # Lesson entity (if applicable)
        if chunk.lesson_number is not None:
            lesson_name = f"Lesson {chunk.lesson_number}"
            lesson_entity_id = self._generate_entity_id(
                f"{chunk.course_title}_{lesson_name}", EntityType.LESSON
            )
            entities.append(
                Entity(
                    id=lesson_entity_id,
                    name=lesson_name,
                    entity_type=EntityType.LESSON,
                    chunk_ids={chunk_id},
                )
            )

        return entities

    def _extract_code_entities(self, content: str, chunk_id: str) -> List[Entity]:
        """Extract entities from code blocks and technical terms"""
        entities = []

        # Extract camelCase identifiers (likely class/function names)
        camelcase_matches = self.patterns["camelcase"].findall(content)
        for match in set(camelcase_matches):  # Remove duplicates
            if len(match) > 3:  # Filter out very short matches
                entity_id = self._generate_entity_id(match, EntityType.CONCEPT)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=match,
                        entity_type=EntityType.CONCEPT,
                        chunk_ids={chunk_id},
                    )
                )

        # Extract ALL_CAPS identifiers (likely constants)
        caps_matches = self.patterns["capitals"].findall(content)
        for match in set(caps_matches):
            if len(match) > 2 and match not in {
                "API",
                "URL",
                "HTTP",
                "JSON",
                "XML",
                "CSS",
                "SQL",
            }:
                entity_id = self._generate_entity_id(match, EntityType.CONCEPT)
                entities.append(
                    Entity(
                        id=entity_id,
                        name=match,
                        entity_type=EntityType.CONCEPT,
                        chunk_ids={chunk_id},
                    )
                )

        return entities

    def extract_relationships(
        self, entities: List[Entity], chunk: CourseChunk
    ) -> List[Relationship]:
        """Extract relationships between entities in a chunk"""
        relationships = []
        chunk_id = f"{chunk.course_title.replace(' ', '_')}_{chunk.chunk_index}"

        # Group entities by type for relationship extraction
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.entity_type].append(entity)

        # Course -> Lesson relationships
        if (
            EntityType.COURSE in entities_by_type
            and EntityType.LESSON in entities_by_type
        ):
            for course_entity in entities_by_type[EntityType.COURSE]:
                for lesson_entity in entities_by_type[EntityType.LESSON]:
                    relationships.append(
                        Relationship(
                            source_entity_id=course_entity.id,
                            target_entity_id=lesson_entity.id,
                            relation_type=RelationType.PART_OF,
                            chunk_ids={chunk_id},
                        )
                    )

        # Course/Lesson -> Technology/Tool/Method relationships
        for course_lesson_type in [EntityType.COURSE, EntityType.LESSON]:
            if course_lesson_type in entities_by_type:
                for content_type in [
                    EntityType.TECHNOLOGY,
                    EntityType.TOOL,
                    EntityType.METHOD,
                ]:
                    if content_type in entities_by_type:
                        for course_lesson_entity in entities_by_type[
                            course_lesson_type
                        ]:
                            for content_entity in entities_by_type[content_type]:
                                relationships.append(
                                    Relationship(
                                        source_entity_id=course_lesson_entity.id,
                                        target_entity_id=content_entity.id,
                                        relation_type=RelationType.TEACHES,
                                        chunk_ids={chunk_id},
                                    )
                                )

        # Technology -> Tool relationships (technologies use tools)
        if (
            EntityType.TECHNOLOGY in entities_by_type
            and EntityType.TOOL in entities_by_type
        ):
            for tech_entity in entities_by_type[EntityType.TECHNOLOGY]:
                for tool_entity in entities_by_type[EntityType.TOOL]:
                    relationships.append(
                        Relationship(
                            source_entity_id=tech_entity.id,
                            target_entity_id=tool_entity.id,
                            relation_type=RelationType.USES,
                            chunk_ids={chunk_id},
                        )
                    )

        # Concept -> Technology/Tool/Method relationships
        if EntityType.CONCEPT in entities_by_type:
            for concept_entity in entities_by_type[EntityType.CONCEPT]:
                for content_type in [
                    EntityType.TECHNOLOGY,
                    EntityType.TOOL,
                    EntityType.METHOD,
                ]:
                    if content_type in entities_by_type:
                        for content_entity in entities_by_type[content_type]:
                            relationships.append(
                                Relationship(
                                    source_entity_id=concept_entity.id,
                                    target_entity_id=content_entity.id,
                                    relation_type=RelationType.RELATES_TO,
                                    chunk_ids={chunk_id},
                                )
                            )

        return relationships

    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """Generate a consistent entity ID based on name and type"""
        # Normalize the name and create a hash for consistency
        normalized_name = name.lower().strip().replace(" ", "_")
        id_string = f"{entity_type.value}_{normalized_name}"
        return hashlib.md5(id_string.encode(), usedforsecurity=False).hexdigest()[:12]

    def merge_entities(self, entity_list: List[List[Entity]]) -> Dict[str, Entity]:
        """Merge entities from multiple chunks, combining chunk_ids"""
        merged_entities = {}

        for entities in entity_list:
            for entity in entities:
                if entity.id in merged_entities:
                    # Merge chunk_ids
                    merged_entities[entity.id].chunk_ids.update(entity.chunk_ids)
                else:
                    merged_entities[entity.id] = entity

        return merged_entities

    def merge_relationships(
        self, relationship_list: List[List[Relationship]]
    ) -> List[Relationship]:
        """Merge relationships from multiple chunks, combining chunk_ids"""
        relationship_map = {}

        for relationships in relationship_list:
            for rel in relationships:
                # Create a key for the relationship
                rel_key = (
                    rel.source_entity_id,
                    rel.target_entity_id,
                    rel.relation_type,
                )

                if rel_key in relationship_map:
                    # Merge chunk_ids
                    relationship_map[rel_key].chunk_ids.update(rel.chunk_ids)
                else:
                    relationship_map[rel_key] = rel

        return list(relationship_map.values())
