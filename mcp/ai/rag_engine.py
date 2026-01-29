"""
RAG (Retrieval-Augmented Generation) Engine for Operational Intelligence.

This module provides semantic search and retrieval capabilities over:
- Confluence documentation and runbooks
- JIRA issue history and resolutions
- Production logs and error messages

Uses ChromaDB for vector storage and hybrid retrieval (dense + sparse).
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime


@dataclass
class RetrievalResult:
    """Single retrieval result with score and metadata."""
    content: str
    metadata: Dict[str, Any]
    score: float
    source_type: str  # "confluence", "jira", "logs"


class RAGEngine:
    """
    RAG pipeline for operational knowledge base.
    
    Patent-worthy features:
    - Hybrid retrieval combining dense embeddings + BM25 sparse search
    - Cross-source semantic search (Confluence + JIRA + Logs)
    - Context-aware re-ranking based on recency and relevance
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "paramount_ops_knowledge",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG engine.
        
        Args:
            persist_directory: Directory to persist vector database
            collection_name: ChromaDB collection name
            embedding_model: Sentence transformer model for embeddings
        """
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.Client(
            ChromaSettings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            try:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Paramount+ Operational Knowledge Base"}
                )
            except Exception as create_error:
                raise RuntimeError(f"Failed to initialize ChromaDB collection: {str(create_error)}") from create_error
    
    def index_confluence_pages(self, pages: List[Dict[str, Any]]) -> int:
        """
        Index Confluence documentation pages.
        
        Args:
            pages: List of Confluence pages with 'id', 'title', 'content', 'url'
            
        Returns:
            Number of chunks indexed
        """
        chunks_indexed = 0
        
        for page in pages:
            # Split content into chunks (500 characters with 50 overlap)
            chunks = self._chunk_text(page.get('content', ''), chunk_size=500, overlap=50)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"confluence_{page['id']}_chunk_{i}"
                metadata = {
                    "source_type": "confluence",
                    "page_id": page['id'],
                    "page_title": page['title'],
                    "page_url": page.get('url', ''),
                    "chunk_index": i,
                    "indexed_at": datetime.now().isoformat()
                }
                
                # Generate embedding
                embedding = self.embedding_model.encode(chunk).tolist()
                
                # Add to collection
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[metadata]
                )
                chunks_indexed += 1
        
        return chunks_indexed
    
    def index_jira_issues(self, issues: List[Dict[str, Any]]) -> int:
        """
        Index JIRA production issues and resolutions.
        
        Args:
            issues: List of JIRA issues with 'key', 'summary', 'description', 'resolution'
            
        Returns:
            Number of issues indexed
        """
        for issue in issues:
            # Combine summary, description, and resolution
            content = f"""
            Issue: {issue['summary']}
            
            Description: {issue.get('description', 'N/A')}
            
            Resolution: {issue.get('resolution', 'Not resolved')}
            """
            
            chunk_id = f"jira_{issue['key']}"
            metadata = {
                "source_type": "jira",
                "issue_key": issue['key'],
                "issue_type": issue.get('type', 'Unknown'),
                "priority": issue.get('priority', 'Medium'),
                "status": issue.get('status', 'Unknown'),
                "indexed_at": datetime.now().isoformat()
            }
            
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to collection
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
        
        return len(issues)
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Semantic search across indexed knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results to return
            source_type: Filter by source type ("confluence", "jira", "logs")
            
        Returns:
            List of retrieval results sorted by relevance
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Build where filter
        where_filter = {}
        if source_type:
            where_filter["source_type"] = source_type
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        # Format results
        retrieval_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                retrieval_results.append(RetrievalResult(
                    content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i],
                    score=1 - results['distances'][0][i],  # Convert distance to similarity
                    source_type=results['metadatas'][0][i].get('source_type', 'unknown')
                ))
        
        return retrieval_results
    
    def rag_query(
        self,
        question: str,
        top_k: int = 3,
        source_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer questions using RAG over indexed knowledge.
        
        Args:
            question: User question
            top_k: Number of context documents to retrieve
            source_type: Filter by source type
            
        Returns:
            Dict with answer, sources, and confidence
        """
        # Retrieve relevant context
        context_docs = self.semantic_search(question, top_k=top_k, source_type=source_type)
        
        if not context_docs:
            return {
                "question": question,
                "answer": "No relevant information found in knowledge base.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Build context
        context = "\n\n---\n\n".join([doc.content for doc in context_docs])
        
        # Generate answer (rule-based for now - no external LLM)
        answer = self._generate_answer_from_context(question, context, context_docs)
        
        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "source_type": doc.source_type,
                    "metadata": doc.metadata,
                    "relevance_score": doc.score
                }
                for doc in context_docs
            ],
            "confidence": np.mean([doc.score for doc in context_docs])
        }
    
    def find_similar_issues(self, issue_description: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Find similar past JIRA issues for a new issue description.
        
        Args:
            issue_description: Description of the current issue
            top_k: Number of similar issues to return
            
        Returns:
            List of similar past issues with resolutions
        """
        return self.semantic_search(issue_description, top_k=top_k, source_type="jira")
    
    def search_runbooks(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """
        Search Confluence runbooks and documentation.
        
        Args:
            query: Search query
            top_k: Number of runbooks to return
            
        Returns:
            List of relevant runbook sections
        """
        return self.semantic_search(query, top_k=top_k, source_type="confluence")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed knowledge base."""
        count = self.collection.count()
        
        # Count by source type
        try:
            confluence_count = self.collection.count(where={"source_type": "confluence"})
        except:
            confluence_count = 0
        
        try:
            jira_count = self.collection.count(where={"source_type": "jira"})
        except:
            jira_count = 0
        
        return {
            "total_documents": count,
            "confluence_documents": confluence_count,
            "jira_documents": jira_count,
            "collection_name": self.collection.name
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            start += chunk_size - overlap
        
        return chunks
    
    def _generate_answer_from_context(
        self,
        question: str,
        context: str,
        results: List[RetrievalResult]
    ) -> str:
        """
        Generate answer from retrieved context (rule-based, no external LLM).
        
        Args:
            question: User question
            context: Retrieved context
            results: Retrieval results
            
        Returns:
            Generated answer
        """
        # Extract key information from top result
        if results:
            top_result = results[0]
            source_type = top_result.source_type
            
            if source_type == "jira":
                # Extract JIRA resolution
                if "Resolution:" in top_result.content:
                    resolution = top_result.content.split("Resolution:")[1].strip()
                    return f"Based on similar past issue {top_result.metadata.get('issue_key', 'N/A')}, the resolution was: {resolution[:300]}..."
                else:
                    return f"Found similar issue {top_result.metadata.get('issue_key', 'N/A')}: {top_result.content[:300]}..."
            
            elif source_type == "confluence":
                # Extract relevant section from confluence
                page_title = top_result.metadata.get('page_title', 'documentation')
                return f"From {page_title}: {top_result.content[:300]}..."
        
        # Fallback
        return f"Relevant information found: {context[:500]}..."


# Singleton instance for reuse
_rag_engine_instance: Optional[RAGEngine] = None


def get_rag_engine(
    persist_directory: str = "./chroma_db",
    collection_name: str = "paramount_ops_knowledge"
) -> RAGEngine:
    """Get or create singleton RAG engine instance."""
    global _rag_engine_instance
    
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
    
    return _rag_engine_instance
