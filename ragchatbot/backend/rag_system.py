import os
from typing import Dict, List, Optional, Tuple

from ai_generator import AIGenerator
from document_processor import DocumentProcessor
from graph_builder import GraphBuilder
from graph_search_tool import GraphEnhancedSearchTool
from graph_store import GraphStore
from models import Course, CourseChunk
from search_tools import CourseSearchTool, ToolManager
from session_manager import SessionManager
from vector_store import VectorStore


class RAGSystem:
    """Main orchestrator for the Retrieval-Augmented Generation system"""

    def __init__(self, config):
        self.config = config

        # Initialize core components
        self.document_processor = DocumentProcessor(
            config.CHUNK_SIZE, config.CHUNK_OVERLAP
        )
        self.vector_store = VectorStore(
            config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS
        )
        self.ai_generator = AIGenerator(
            config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL
        )
        self.session_manager = SessionManager(config.MAX_HISTORY)

        # Initialize GraphRAG components
        self.graph_builder = GraphBuilder()
        self.graph_store = None
        self.graph_enabled = getattr(config, "ENABLE_GRAPHRAG", True)

        # Initialize search tools
        self.tool_manager = ToolManager()

        # Use GraphRAG search tool if enabled, otherwise use traditional search
        if self.graph_enabled:
            self.search_tool = GraphEnhancedSearchTool(self.vector_store)
            # Try to load existing graph data
            self._load_graph_data()
        else:
            self.search_tool = CourseSearchTool(self.vector_store)

        self.tool_manager.register_tool(self.search_tool)

    def add_course_document(self, file_path: str) -> Tuple[Course, int]:
        """
        Add a single course document to the knowledge base.

        Args:
            file_path: Path to the course document

        Returns:
            Tuple of (Course object, number of chunks created)
        """
        try:
            # Process the document
            course, course_chunks = self.document_processor.process_course_document(
                file_path
            )

            # Add course metadata to vector store for semantic search
            self.vector_store.add_course_metadata(course)

            # Add course content chunks to vector store
            self.vector_store.add_course_content(course_chunks)

            return course, len(course_chunks)
        except Exception as e:
            print(f"Error processing course document {file_path}: {e}")
            return None, 0

    def add_course_folder(
        self, folder_path: str, clear_existing: bool = False
    ) -> Tuple[int, int]:
        """
        Add all course documents from a folder.

        Args:
            folder_path: Path to folder containing course documents
            clear_existing: Whether to clear existing data first

        Returns:
            Tuple of (total courses added, total chunks created)
        """
        total_courses = 0
        total_chunks = 0
        all_new_chunks = []

        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing data for fresh rebuild...")
            self.vector_store.clear_all_data()
            if self.graph_enabled:
                self.graph_builder.clear_graph()

        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} does not exist")
            return 0, 0

        # Get existing course titles to avoid re-processing
        existing_course_titles = set(self.vector_store.get_existing_course_titles())

        # Process each file in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(
                (".pdf", ".docx", ".txt")
            ):
                try:
                    # Check if this course might already exist
                    # We'll process the document to get the course ID, but only add
                    # if new
                    course, course_chunks = (
                        self.document_processor.process_course_document(file_path)
                    )

                    if course and course.title not in existing_course_titles:
                        # This is a new course - add it to the vector store
                        self.vector_store.add_course_metadata(course)
                        self.vector_store.add_course_content(course_chunks)
                        total_courses += 1
                        total_chunks += len(course_chunks)
                        all_new_chunks.extend(course_chunks)
                        print(
                            f"Added new course: {course.title} "
                            f"({len(course_chunks)} chunks)"
                        )
                        existing_course_titles.add(course.title)
                    elif course:
                        print(f"Course already exists: {course.title} - skipping")
                except Exception as e:
                    print(f"Error processing {file_name}: {e}")

        # Build or update knowledge graph if GraphRAG is enabled
        if self.graph_enabled and all_new_chunks:
            self._build_or_update_graph(all_new_chunks, clear_existing)

        return total_courses, total_chunks

    def query(
        self, query: str, session_id: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Process a user query using the RAG system with tool-based search.

        Args:
            query: User's question
            session_id: Optional session ID for conversation context

        Returns:
            Tuple of (response, sources list - empty for tool-based approach)
        """
        # Create prompt for the AI with clear instructions
        prompt = f"""Answer this question about course materials: {query}"""

        # Get conversation history if session exists
        history = None
        if session_id:
            history = self.session_manager.get_conversation_history(session_id)

        # Generate response using AI with tools
        response = self.ai_generator.generate_response(
            query=prompt,
            conversation_history=history,
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager,
        )

        # Get sources from the search tool
        sources = self.tool_manager.get_last_sources()

        # Reset sources after retrieving them
        self.tool_manager.reset_sources()

        # Update conversation history
        if session_id:
            self.session_manager.add_exchange(session_id, query, response)

        # Return response with sources from tool searches
        return response, sources

    def get_course_analytics(self) -> Dict:
        """Get analytics about the course catalog"""
        analytics = {
            "total_courses": self.vector_store.get_course_count(),
            "course_titles": self.vector_store.get_existing_course_titles(),
            "graph_enabled": self.graph_enabled,
        }

        # Add graph analytics if available
        if self.graph_enabled and self.graph_store:
            try:
                graph_stats = self.graph_store.get_statistics()
                analytics["graph_statistics"] = graph_stats
            except Exception as e:
                print(f"Error getting graph statistics: {e}")

        return analytics

    def _load_graph_data(self):
        """Load existing graph data from vector store"""
        if not self.graph_enabled:
            return

        try:
            graph_json = self.vector_store.load_graph_data()
            if graph_json:
                print("Loading existing knowledge graph...")
                self.graph_store = GraphStore()
                self.graph_store.load_from_json(graph_json)
                self.search_tool.set_graph_store(self.graph_store)
                print(f"Graph loaded: {self.graph_store.get_statistics()}")
            else:
                print("No existing graph data found")
        except Exception as e:
            print(f"Error loading graph data: {e}")

    def _build_or_update_graph(self, chunks: List[CourseChunk], rebuild: bool = False):
        """Build or update the knowledge graph with new chunks"""
        if not self.graph_enabled:
            return

        try:
            if rebuild or not self.graph_store:
                # Build fresh graph
                print("Building knowledge graph from scratch...")
                self.graph_store = self.graph_builder.build_graph_from_chunks(chunks)
            else:
                # Update existing graph
                print("Updating knowledge graph with new chunks...")
                self.graph_store = self.graph_builder.update_graph_with_new_chunks(
                    chunks, self.graph_store
                )

            # Save graph data to vector store
            graph_json = self.graph_store.serialize_to_json()
            self.vector_store.store_graph_data(graph_json)

            # Update search tool with new graph
            self.search_tool.set_graph_store(self.graph_store)

            print("Knowledge graph updated successfully!")

        except Exception as e:
            print(f"Error building/updating graph: {e}")

    def rebuild_knowledge_graph(self):
        """Rebuild the entire knowledge graph from existing chunks"""
        if not self.graph_enabled:
            print("GraphRAG is not enabled")
            return

        try:
            # Get all chunks from vector store
            print("Retrieving all chunks for graph rebuild...")
            all_results = self.vector_store.course_content.get()

            if not all_results or not all_results.get("documents"):
                print("No chunks found to build graph")
                return

            # Convert results back to CourseChunk objects
            chunks = []
            for i, (doc, metadata) in enumerate(
                zip(all_results["documents"], all_results["metadatas"])
            ):
                chunk = CourseChunk(
                    content=doc,
                    course_title=metadata.get("course_title", "Unknown"),
                    lesson_number=metadata.get("lesson_number"),
                    chunk_index=metadata.get("chunk_index", i),
                )
                chunks.append(chunk)

            # Rebuild graph
            self._build_or_update_graph(chunks, rebuild=True)

        except Exception as e:
            print(f"Error rebuilding knowledge graph: {e}")

    def get_graph_summary(self) -> Dict:
        """Get a summary of the knowledge graph"""
        if not self.graph_enabled or not self.graph_store:
            return {"error": "Knowledge graph not available"}

        try:
            return self.graph_builder.get_graph_summary()
        except Exception as e:
            return {"error": f"Error getting graph summary: {e}"}

    def find_entity_connections(self, entity_name: str) -> Dict:
        """Find connections for a specific entity in the knowledge graph"""
        if not self.graph_enabled or not self.graph_store:
            return {"error": "Knowledge graph not available"}

        try:
            return self.graph_builder.get_entity_connections(entity_name)
        except Exception as e:
            return {"error": f"Error finding entity connections: {e}"}
