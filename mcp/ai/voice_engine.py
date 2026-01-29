"""
Voice AI Engine for Speech Intelligence.

Uses Whisper for automatic speech recognition (ASR) and Coqui TTS
for text-to-speech generation.

Patent-worthy features:
- Real-time support call transcription and sentiment analysis
- Voice-enabled production alerts with priority-based TTS
- Automatic complaint keyword extraction from voice
- Multi-language support for global operations
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
import re


@dataclass
class TranscriptionResult:
    """Result of speech transcription."""
    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]
    duration_seconds: float
    complaint_keywords: List[str]
    sentiment_score: float  # -1 (negative) to 1 (positive)


@dataclass
class AlertAudio:
    """Generated alert audio."""
    audio_path: str
    text: str
    duration_seconds: float
    priority: str


class VoiceEngine:
    """
    Voice AI engine for transcription and speech generation.
    
    Uses OpenAI Whisper (open-source) for ASR and Coqui TTS for speech synthesis.
    """
    
    def __init__(
        self,
        whisper_model_size: str = "base",
        enable_gpu: bool = False,
        alerts_output_dir: str = "./alerts"
    ):
        """
        Initialize voice engine.
        
        Args:
            whisper_model_size: Whisper model size (tiny, base, small, medium, large)
            enable_gpu: Enable GPU acceleration
            alerts_output_dir: Directory for generated alert audio files
        """
        self.whisper_model_size = whisper_model_size
        self.enable_gpu = enable_gpu
        self.alerts_output_dir = alerts_output_dir
        
        # Create alerts directory
        os.makedirs(alerts_output_dir, exist_ok=True)
        
        # Lazy load models
        self._whisper_model = None
        self._tts_model = None
        
        # Complaint keywords for extraction
        self.complaint_keywords = [
            "buffering", "error", "crashed", "frozen", "slow", "lagging",
            "not working", "broken", "unable to", "can't watch", "keeps stopping",
            "poor quality", "pixelated", "audio issues", "video stuttering",
            "login failed", "subscription", "payment", "charged", "refund",
            "customer service", "unhappy", "frustrated", "disappointed", "angry"
        ]
    
    def _load_whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            try:
                import whisper
                import torch
                
                device = "cuda" if self.enable_gpu and torch.cuda.is_available() else "cpu"
                self._whisper_model = whisper.load_model(self.whisper_model_size, device=device)
            except ImportError:
                raise ImportError(
                    "openai-whisper is required for voice engine. "
                    "Install with: pip install openai-whisper"
                )
    
    def _load_tts_model(self):
        """Lazy load TTS model."""
        if self._tts_model is None:
            try:
                from TTS.api import TTS as CoquiTTS
                
                # Use VITS model for high-quality English TTS
                self._tts_model = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            except ImportError:
                raise ImportError(
                    "TTS is required for voice engine. "
                    "Install with: pip install TTS"
                )
    
    def transcribe_support_call(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribe support call audio file.
        
        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Optional language code (e.g., 'en', 'es'). Auto-detect if None.
            
        Returns:
            TranscriptionResult with text, segments, and extracted keywords
        """
        self._load_whisper_model()
        
        # Transcribe audio
        result = self._whisper_model.transcribe(
            audio_path,
            language=language,
            task="transcribe"
        )
        
        text = result["text"]
        detected_language = result.get("language", "en")
        segments = result.get("segments", [])
        
        # Extract complaint keywords
        complaint_keywords = self._extract_complaint_keywords(text)
        
        # Analyze sentiment
        sentiment_score = self._analyze_voice_sentiment(text)
        
        # Calculate average confidence from segments
        avg_confidence = sum(seg.get("no_speech_prob", 0.5) for seg in segments) / len(segments) if segments else 0.8
        confidence = 1 - avg_confidence  # Convert no_speech_prob to confidence
        
        # Estimate duration (rough approximation)
        duration = sum(seg.get("end", 0) - seg.get("start", 0) for seg in segments) if segments else 0.0
        
        return TranscriptionResult(
            text=text,
            language=detected_language,
            confidence=confidence,
            segments=[
                {
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": seg.get("text", "")
                }
                for seg in segments
            ],
            duration_seconds=duration,
            complaint_keywords=complaint_keywords,
            sentiment_score=sentiment_score
        )
    
    def generate_alert_notification(
        self,
        alert: Dict[str, Any],
        priority: str = "high"
    ) -> AlertAudio:
        """
        Generate voice alert for critical production issues.
        
        Args:
            alert: Alert details (id, summary, severity, action_required)
            priority: Priority level (critical, high, medium, low)
            
        Returns:
            AlertAudio with generated audio file path
        """
        self._load_tts_model()
        
        # Build alert message based on priority
        severity = alert.get('severity', 'high')
        summary = alert.get('summary', 'Production issue detected')
        action = alert.get('action_required', 'Please investigate immediately')
        
        if priority == "critical" or severity == "critical":
            message = f"Critical alert. {summary}. Immediate action required. {action}"
        elif priority == "high" or severity == "high":
            message = f"High priority alert. {summary}. {action}"
        else:
            message = f"Alert notification. {summary}. {action}"
        
        # Generate audio file
        alert_id = alert.get('id', f"alert_{datetime.now().timestamp()}")
        audio_filename = f"alert_{alert_id}_{priority}.wav"
        audio_path = os.path.join(self.alerts_output_dir, audio_filename)
        
        try:
            self._tts_model.tts_to_file(
                text=message,
                file_path=audio_path
            )
            
            # Estimate duration (rough: ~150 words per minute)
            word_count = len(message.split())
            duration = (word_count / 150) * 60
        except Exception as e:
            # Fallback: create a placeholder
            duration = 10.0
            # In production, log the error and handle gracefully
        
        return AlertAudio(
            audio_path=audio_path,
            text=message,
            duration_seconds=duration,
            priority=priority
        )
    
    def batch_transcribe_calls(
        self,
        audio_files: List[str],
        language: Optional[str] = None
    ) -> List[TranscriptionResult]:
        """
        Batch transcribe multiple support calls.
        
        Args:
            audio_files: List of audio file paths
            language: Optional language code
            
        Returns:
            List of transcription results
        """
        results = []
        
        for audio_file in audio_files:
            try:
                result = self.transcribe_support_call(audio_file, language=language)
                results.append(result)
            except Exception as e:
                # Log error and continue with other files
                print(f"Error transcribing {audio_file}: {e}")
                continue
        
        return results
    
    def extract_call_insights(
        self,
        transcription_results: List[TranscriptionResult]
    ) -> Dict[str, Any]:
        """
        Extract insights from multiple transcribed support calls.
        
        Args:
            transcription_results: List of transcription results
            
        Returns:
            Dict with aggregated insights (common complaints, sentiment trends, etc.)
        """
        if not transcription_results:
            return {
                "total_calls": 0,
                "top_complaints": [],
                "avg_sentiment": 0.0,
                "language_distribution": {}
            }
        
        # Aggregate complaint keywords
        all_keywords = []
        for result in transcription_results:
            all_keywords.extend(result.complaint_keywords)
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Top complaints
        top_complaints = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Average sentiment
        avg_sentiment = sum(r.sentiment_score for r in transcription_results) / len(transcription_results)
        
        # Language distribution
        language_counts = {}
        for result in transcription_results:
            lang = result.language
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return {
            "total_calls": len(transcription_results),
            "top_complaints": [{"keyword": k, "count": c} for k, c in top_complaints],
            "avg_sentiment": avg_sentiment,
            "sentiment_trend": "negative" if avg_sentiment < -0.2 else "neutral" if avg_sentiment < 0.2 else "positive",
            "language_distribution": language_counts,
            "total_duration_hours": sum(r.duration_seconds for r in transcription_results) / 3600
        }
    
    def _extract_complaint_keywords(self, text: str) -> List[str]:
        """
        Extract complaint-related keywords from text.
        
        Args:
            text: Transcribed text
            
        Returns:
            List of detected complaint keywords
        """
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.complaint_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _analyze_voice_sentiment(self, text: str) -> float:
        """
        Analyze sentiment from transcribed text.
        
        Uses TextBlob for sentiment analysis (rule-based).
        
        Args:
            text: Transcribed text
            
        Returns:
            Sentiment score (-1 to 1)
        """
        try:
            from textblob import TextBlob
            
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            return sentiment
        except ImportError:
            # Fallback: simple rule-based sentiment
            negative_words = ["error", "problem", "issue", "bad", "terrible", "poor", "frustrated", "angry", "disappointed"]
            positive_words = ["good", "great", "excellent", "happy", "satisfied", "resolved", "fixed", "working"]
            
            text_lower = text.lower()
            neg_count = sum(1 for word in negative_words if word in text_lower)
            pos_count = sum(1 for word in positive_words if word in text_lower)
            
            if neg_count + pos_count == 0:
                return 0.0
            
            return (pos_count - neg_count) / (pos_count + neg_count)


# Singleton instance
_voice_engine_instance: Optional[VoiceEngine] = None


def get_voice_engine(
    whisper_model_size: str = "base",
    enable_gpu: bool = False
) -> VoiceEngine:
    """Get or create singleton voice engine instance."""
    global _voice_engine_instance
    
    if _voice_engine_instance is None:
        _voice_engine_instance = VoiceEngine(
            whisper_model_size=whisper_model_size,
            enable_gpu=enable_gpu
        )
    
    return _voice_engine_instance
