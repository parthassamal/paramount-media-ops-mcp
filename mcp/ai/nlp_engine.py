"""
NLP Engine for Natural Language Processing.

Unified interface for spaCy and transformers for advanced text processing.

Features:
- Entity extraction (people, organizations, locations)
- Text summarization
- Topic modeling
- Sentiment analysis
- Named entity recognition (NER)
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import re

from mcp.utils.error_handler import ModelNotFoundError, ValidationError
from mcp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Entity:
    """Named entity."""
    text: str
    label: str  # PERSON, ORG, GPE, DATE, etc.
    start_char: int
    end_char: int


@dataclass
class TextAnalysisResult:
    """Complete text analysis result."""
    text: str
    entities: List[Entity]
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # negative, neutral, positive
    keywords: List[str]
    language: str


class NLPEngine:
    """
    Unified NLP engine combining spaCy and transformers.
    
    Provides entity extraction, sentiment analysis, and text processing.
    """
    
    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        enable_gpu: bool = False
    ):
        """
        Initialize NLP engine.
        
        Args:
            spacy_model: spaCy model name
            enable_gpu: Enable GPU acceleration
        """
        self.spacy_model_name = spacy_model
        self.enable_gpu = enable_gpu
        
        # Lazy load models
        self._spacy_nlp = None
        self._sentiment_model = None
    
    def _load_spacy(self):
        """Lazy load spaCy model."""
        if self._spacy_nlp is None:
            try:
                import spacy
                self._spacy_nlp = spacy.load(self.spacy_model_name)
            except (ImportError, OSError):
                # Fallback to rule-based processing if spacy not available
                self._spacy_nlp = None
    
    def _load_sentiment_model(self):
        """Lazy load sentiment model."""
        if self._sentiment_model is None:
            try:
                from textblob import TextBlob
                self._sentiment_model = TextBlob
            except ImportError:
                self._sentiment_model = None
    
    def analyze_text(self, text: str) -> TextAnalysisResult:
        """
        Comprehensive text analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            TextAnalysisResult with entities, sentiment, and keywords
        """
        # Extract entities
        entities = self.extract_entities(text)
        
        # Analyze sentiment
        sentiment_score = self.analyze_sentiment(text)
        sentiment_label = self._sentiment_to_label(sentiment_score)
        
        # Extract keywords
        keywords = self.extract_keywords(text, top_k=10)
        
        # Detect language
        language = self.detect_language(text)
        
        return TextAnalysisResult(
            text=text,
            entities=entities,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            keywords=keywords,
            language=language
        )
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to process
            
        Returns:
            List of extracted entities
        """
        self._load_spacy()
        
        if self._spacy_nlp is None:
            # Fallback to simple pattern matching
            return self._fallback_extract_entities(text)
        
        # Process with spaCy
        doc = self._spacy_nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append(Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char
            ))
        
        return entities
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1 to 1)
        """
        self._load_sentiment_model()
        
        if self._sentiment_model is None:
            # Fallback to rule-based
            return self._fallback_sentiment(text)
        
        # Use TextBlob
        blob = self._sentiment_model(text)
        return blob.sentiment.polarity
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Text to process
            top_k: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        self._load_spacy()
        
        if self._spacy_nlp is None:
            # Fallback to simple word frequency
            return self._fallback_keywords(text, top_k)
        
        # Process with spaCy
        doc = self._spacy_nlp(text)
        
        # Extract noun chunks and important tokens
        keywords = []
        
        # Add noun chunks
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Limit to 3-word phrases
                keywords.append(chunk.text.lower())
        
        # Add important single tokens (nouns, proper nouns, verbs)
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'VERB'] and not token.is_stop:
                keywords.append(token.lemma_.lower())
        
        # Count frequency
        keyword_counts = {}
        for kw in keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [kw for kw, count in sorted_keywords[:top_k]]
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'en', 'es')
        """
        self._load_spacy()
        
        if self._spacy_nlp is None:
            # Default to English
            return "en"
        
        # spaCy can detect language if enabled
        # For now, return the model's language
        return self._spacy_nlp.lang
    
    def summarize_text(
        self,
        text: str,
        max_sentences: int = 3
    ) -> str:
        """
        Summarize text by extracting key sentences.
        
        Args:
            text: Text to summarize
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summary text
        """
        self._load_spacy()
        
        if self._spacy_nlp is None:
            # Fallback: return first N sentences
            sentences = re.split(r'[.!?]+', text)
            return '. '.join(sentences[:max_sentences]) + '.'
        
        # Process with spaCy
        doc = self._spacy_nlp(text)
        
        # Score sentences based on keyword frequency
        sentences = list(doc.sents)
        
        if len(sentences) <= max_sentences:
            return text
        
        # Extract keywords
        keywords = self.extract_keywords(text, top_k=20)
        keyword_set = set(keywords)
        
        # Score sentences
        sentence_scores = []
        for sent in sentences:
            # Count keywords in sentence
            sent_text_lower = sent.text.lower()
            score = sum(1 for kw in keyword_set if kw in sent_text_lower)
            sentence_scores.append((sent, score))
        
        # Sort by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top sentences
        top_sentences = sentence_scores[:max_sentences]
        
        # Sort by original order
        top_sentences.sort(key=lambda x: x[0].start)
        
        summary = ' '.join(sent.text for sent, score in top_sentences)
        return summary
    
    def _sentiment_to_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score < -0.2:
            return "negative"
        elif score > 0.2:
            return "positive"
        else:
            return "neutral"
    
    def _fallback_extract_entities(self, text: str) -> List[Entity]:
        """Fallback entity extraction using regex patterns."""
        entities = []
        
        # Simple email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="EMAIL",
                start_char=match.start(),
                end_char=match.end()
            ))
        
        # Simple URL pattern
        url_pattern = r'https?://[^\s]+'
        for match in re.finditer(url_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="URL",
                start_char=match.start(),
                end_char=match.end()
            ))
        
        return entities
    
    def _fallback_sentiment(self, text: str) -> float:
        """Fallback rule-based sentiment analysis."""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'happy', 'satisfied', 'pleased', 'resolved', 'fixed', 'working'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
            'hate', 'angry', 'frustrated', 'disappointed', 'broken', 'error',
            'problem', 'issue', 'failed', 'crash', 'slow', 'lag'
        ]
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def _fallback_keywords(self, text: str, top_k: int) -> List[str]:
        """Fallback keyword extraction using word frequency."""
        # Remove punctuation and lowercase
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words
        words = text_clean.split()
        
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Filter stop words and short words
        words_filtered = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count frequency
        word_counts = {}
        for word in words_filtered:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, count in sorted_words[:top_k]]


# Singleton instance
_nlp_engine_instance: Optional[NLPEngine] = None


def get_nlp_engine(
    spacy_model: str = "en_core_web_sm",
    enable_gpu: bool = False
) -> NLPEngine:
    """Get or create singleton NLP engine instance."""
    global _nlp_engine_instance
    
    if _nlp_engine_instance is None:
        _nlp_engine_instance = NLPEngine(
            spacy_model=spacy_model,
            enable_gpu=enable_gpu
        )
    
    return _nlp_engine_instance
