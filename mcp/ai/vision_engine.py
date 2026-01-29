"""
Computer Vision Engine for Content Intelligence.

Uses CLIP (Contrastive Language-Image Pre-training) for zero-shot
image classification and content analysis.

Patent-worthy features:
- Zero-shot content categorization without training data
- Quality assessment pipeline for streaming thumbnails
- Visual similarity search for content recommendations
- Automated compliance checking (brand guidelines, content policy)
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np
from io import BytesIO
import os


@dataclass
class ContentAnalysisResult:
    """Result of content analysis."""
    predicted_category: str
    confidence: float
    all_scores: Dict[str, float]
    quality_score: float
    quality_issues: List[Dict[str, Any]]


@dataclass
class QualityIssue:
    """Quality issue detected in content."""
    issue_type: str
    severity: str  # "low", "medium", "high"
    confidence: float
    description: str


class VisionEngine:
    """
    Computer vision engine for content analysis and moderation.
    
    Uses CLIP for image-text understanding without training.
    """
    
    def __init__(
        self,
        clip_model_name: str = "ViT-B/32",
        enable_gpu: bool = False
    ):
        """
        Initialize vision engine.
        
        Args:
            clip_model_name: CLIP model variant
            enable_gpu: Enable GPU acceleration (requires CUDA)
        """
        self.clip_model_name = clip_model_name
        self.enable_gpu = enable_gpu
        
        # Lazy load models (on first use)
        self._clip_model = None
        self._clip_processor = None
    
    def _load_clip_model(self):
        """Lazy load CLIP model."""
        if self._clip_model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                import torch
                
                self._clip_model = CLIPModel.from_pretrained(f"openai/clip-vit-base-patch32")
                self._clip_processor = CLIPProcessor.from_pretrained(f"openai/clip-vit-base-patch32")
                
                # Move to GPU if enabled and available
                if self.enable_gpu and torch.cuda.is_available():
                    self._clip_model = self._clip_model.cuda()
            except ImportError:
                raise ImportError(
                    "transformers and torch are required for vision engine. "
                    "Install with: pip install transformers torch"
                )
    
    def analyze_content_thumbnail(
        self,
        image_path: str,
        categories: Optional[List[str]] = None
    ) -> ContentAnalysisResult:
        """
        Analyze content thumbnail using zero-shot classification.
        
        Args:
            image_path: Path to image file
            categories: Optional list of categories (uses defaults if None)
            
        Returns:
            ContentAnalysisResult with predicted category and scores
        """
        self._load_clip_model()
        
        # Default Paramount+ content categories
        if categories is None:
            categories = [
                "action movie",
                "drama series",
                "comedy show",
                "sports content",
                "reality tv",
                "documentary",
                "kids content",
                "news program",
                "talk show",
                "live event"
            ]
        
        # Load image
        image = Image.open(image_path).convert("RGB")
        
        # CLIP zero-shot classification
        import torch
        
        inputs = self._clip_processor(
            text=categories,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        # Move to GPU if enabled
        if self.enable_gpu and torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = self._clip_model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        # Convert to numpy
        probs_np = probs.cpu().detach().numpy()[0]
        
        # Get predicted category
        predicted_idx = int(np.argmax(probs_np))
        predicted_category = categories[predicted_idx]
        confidence = float(probs_np[predicted_idx])
        
        # Build scores dict
        all_scores = {cat: float(score) for cat, score in zip(categories, probs_np)}
        
        # Quality assessment
        quality_score, quality_issues = self._assess_image_quality(image)
        
        return ContentAnalysisResult(
            predicted_category=predicted_category,
            confidence=confidence,
            all_scores=all_scores,
            quality_score=quality_score,
            quality_issues=[{"issue": q.issue_type, "severity": q.severity, "confidence": q.confidence} for q in quality_issues]
        )
    
    def detect_quality_issues(
        self,
        image_path: str,
        check_types: Optional[List[str]] = None
    ) -> List[QualityIssue]:
        """
        Detect quality issues in content thumbnails.
        
        Args:
            image_path: Path to image file
            check_types: Optional list of check types
            
        Returns:
            List of detected quality issues
        """
        self._load_clip_model()
        
        # Default quality checks
        if check_types is None:
            check_types = [
                "blurry image",
                "low resolution",
                "poor lighting",
                "text overlapping",
                "brand guidelines violation",
                "inappropriate content",
                "color balance issues"
            ]
        
        # Load image
        image = Image.open(image_path).convert("RGB")
        
        # CLIP classification for quality issues
        import torch
        
        inputs = self._clip_processor(
            text=check_types,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if self.enable_gpu and torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = self._clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
        probs_np = probs.cpu().detach().numpy()[0]
        
        # Detect issues (threshold = 0.3)
        issues = []
        for check, score in zip(check_types, probs_np):
            if float(score) > 0.3:
                severity = "high" if score > 0.7 else "medium" if score > 0.5 else "low"
                issues.append(QualityIssue(
                    issue_type=check,
                    severity=severity,
                    confidence=float(score),
                    description=f"Detected {check} with {score:.0%} confidence"
                ))
        
        return issues
    
    def _assess_image_quality(self, image: Image.Image) -> Tuple[float, List[QualityIssue]]:
        """
        Assess overall image quality using multiple heuristics.
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (quality_score, quality_issues)
        """
        issues = []
        quality_score = 1.0
        
        # Check resolution
        width, height = image.size
        if width < 640 or height < 480:
            issues.append(QualityIssue(
                issue_type="low_resolution",
                severity="high",
                confidence=0.9,
                description=f"Resolution {width}x{height} below recommended 640x480"
            ))
            quality_score -= 0.3
        
        # Check aspect ratio
        aspect_ratio = width / height
        if not (1.3 < aspect_ratio < 2.0):  # Standard video aspect ratios: 4:3 to 16:9
            issues.append(QualityIssue(
                issue_type="unusual_aspect_ratio",
                severity="medium",
                confidence=0.8,
                description=f"Aspect ratio {aspect_ratio:.2f} outside standard range"
            ))
            quality_score -= 0.2
        
        # Check for blank/uniform images
        img_array = np.array(image)
        if img_array.std() < 10:  # Very low variance = likely blank
            issues.append(QualityIssue(
                issue_type="low_detail",
                severity="high",
                confidence=0.95,
                description="Image appears blank or has very low detail"
            ))
            quality_score -= 0.4
        
        return max(0.0, quality_score), issues
    
    def compare_images_similarity(
        self,
        image_path_1: str,
        image_path_2: str
    ) -> float:
        """
        Compare visual similarity between two images using CLIP embeddings.
        
        Args:
            image_path_1: Path to first image
            image_path_2: Path to second image
            
        Returns:
            Similarity score (0-1, higher = more similar)
        """
        self._load_clip_model()
        
        import torch
        
        # Load images
        image1 = Image.open(image_path_1).convert("RGB")
        image2 = Image.open(image_path_2).convert("RGB")
        
        # Get CLIP embeddings
        inputs1 = self._clip_processor(images=image1, return_tensors="pt")
        inputs2 = self._clip_processor(images=image2, return_tensors="pt")
        
        if self.enable_gpu and torch.cuda.is_available():
            inputs1 = {k: v.cuda() for k, v in inputs1.items()}
            inputs2 = {k: v.cuda() for k, v in inputs2.items()}
        
        with torch.no_grad():
            embedding1 = self._clip_model.get_image_features(**inputs1)
            embedding2 = self._clip_model.get_image_features(**inputs2)
        
        # Normalize
        embedding1 = embedding1 / embedding1.norm(dim=-1, keepdim=True)
        embedding2 = embedding2 / embedding2.norm(dim=-1, keepdim=True)
        
        # Cosine similarity
        similarity = (embedding1 @ embedding2.T).cpu().item()
        
        return float(similarity)
    
    def find_similar_content(
        self,
        query_image_path: str,
        content_library: List[Dict[str, str]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find visually similar content in library using CLIP embeddings.
        
        Args:
            query_image_path: Path to query image
            content_library: List of content items with 'id' and 'thumbnail_path'
            top_k: Number of similar items to return
            
        Returns:
            List of similar content items with similarity scores
        """
        # Calculate similarities
        similarities = []
        for content in content_library:
            try:
                similarity = self.compare_images_similarity(
                    query_image_path,
                    content['thumbnail_path']
                )
                similarities.append({
                    "content_id": content['id'],
                    "similarity_score": similarity,
                    "metadata": content
                })
            except Exception as e:
                # Skip if image can't be loaded
                continue
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similarities[:top_k]
    
    def check_brand_compliance(
        self,
        image_path: str,
        brand_guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if image complies with brand guidelines.
        
        Args:
            image_path: Path to image
            brand_guidelines: Dict with brand requirements
            
        Returns:
            Compliance result with violations
        """
        # Load image
        image = Image.open(image_path)
        
        violations = []
        compliance_score = 1.0
        
        # Check dimensions
        required_min_width = brand_guidelines.get('min_width', 1920)
        required_min_height = brand_guidelines.get('min_height', 1080)
        
        width, height = image.size
        if width < required_min_width or height < required_min_height:
            violations.append({
                "rule": "minimum_dimensions",
                "severity": "high",
                "message": f"Image {width}x{height} below required {required_min_width}x{required_min_height}"
            })
            compliance_score -= 0.3
        
        # Check aspect ratio
        required_aspect_ratio = brand_guidelines.get('aspect_ratio', 16/9)
        tolerance = brand_guidelines.get('aspect_ratio_tolerance', 0.1)
        
        actual_aspect_ratio = width / height
        if abs(actual_aspect_ratio - required_aspect_ratio) > tolerance:
            violations.append({
                "rule": "aspect_ratio",
                "severity": "medium",
                "message": f"Aspect ratio {actual_aspect_ratio:.2f} deviates from required {required_aspect_ratio:.2f}"
            })
            compliance_score -= 0.2
        
        return {
            "compliant": len(violations) == 0,
            "compliance_score": max(0.0, compliance_score),
            "violations": violations,
            "image_dimensions": {"width": width, "height": height}
        }


# Singleton instance
_vision_engine_instance: Optional[VisionEngine] = None


def get_vision_engine(enable_gpu: bool = False) -> VisionEngine:
    """Get or create singleton vision engine instance."""
    global _vision_engine_instance
    
    if _vision_engine_instance is None:
        _vision_engine_instance = VisionEngine(enable_gpu=enable_gpu)
    
    return _vision_engine_instance
