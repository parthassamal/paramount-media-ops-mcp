"""
Pareto Analysis Calculator for 80/20 decomposition.

This module implements the Pareto principle (80/20 rule) to identify
the vital few factors that drive the majority of impact in operations data.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class ParetoResult:
    """Result of Pareto analysis."""
    
    top_20_percent_indices: List[int]
    top_20_percent_contribution: float
    cumulative_contributions: List[float]
    sorted_items: List[Dict[str, Any]]
    total_impact: float
    is_pareto_valid: bool  # True if top 20% contributes 75-85%
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "top_20_percent_indices": self.top_20_percent_indices,
            "top_20_percent_contribution": round(self.top_20_percent_contribution, 4),
            "cumulative_contributions": [round(c, 4) for c in self.cumulative_contributions],
            "sorted_items": self.sorted_items,
            "total_impact": round(self.total_impact, 2),
            "is_pareto_valid": self.is_pareto_valid,
            "validation_message": self._get_validation_message()
        }
    
    def _get_validation_message(self) -> str:
        """Get validation message based on Pareto principle."""
        contribution_pct = self.top_20_percent_contribution * 100
        if 75 <= contribution_pct <= 85:
            return f"✅ Pareto principle validated: Top 20% drives {contribution_pct:.1f}% of impact"
        elif contribution_pct > 85:
            return f"⚠️  High concentration: Top 20% drives {contribution_pct:.1f}% (>85%)"
        else:
            return f"⚠️  Low concentration: Top 20% drives only {contribution_pct:.1f}% (<75%)"


class ParetoCalculator:
    """
    Calculator for Pareto analysis (80/20 decomposition).
    
    The Pareto principle states that roughly 80% of consequences come from 20%
    of causes. This calculator identifies the top 20% of items that drive the
    majority of impact.
    
    Examples:
        >>> calculator = ParetoCalculator()
        >>> items = [
        ...     {"id": "issue_1", "delay_days": 45},
        ...     {"id": "issue_2", "delay_days": 30},
        ...     {"id": "issue_3", "delay_days": 5}
        ... ]
        >>> result = calculator.analyze(items, impact_field="delay_days")
        >>> print(result.top_20_percent_contribution)
        0.75
    """
    
    def __init__(self, pareto_threshold: float = 0.80, validation_range: Tuple[float, float] = (0.75, 0.85)):
        """
        Initialize Pareto calculator.
        
        Args:
            pareto_threshold: Target threshold for Pareto principle (default: 0.80)
            validation_range: Valid range for Pareto validation (default: 75-85%)
        """
        self.pareto_threshold = pareto_threshold
        self.validation_range = validation_range
    
    def analyze(
        self,
        items: List[Dict[str, Any]],
        impact_field: str,
        id_field: str = "id",
        ascending: bool = False
    ) -> ParetoResult:
        """
        Perform Pareto analysis on a list of items.
        
        Args:
            items: List of dictionaries containing data to analyze
            impact_field: Field name to use for impact measurement
            id_field: Field name to use as identifier (default: "id")
            ascending: If True, sort in ascending order (default: False for descending)
        
        Returns:
            ParetoResult containing analysis results
        
        Raises:
            ValueError: If items is empty or impact_field doesn't exist
        """
        if not items:
            raise ValueError("Cannot perform Pareto analysis on empty list")
        
        if impact_field not in items[0]:
            raise ValueError(f"Impact field '{impact_field}' not found in items")
        
        # Extract impact values
        impacts = np.array([item.get(impact_field, 0) for item in items])
        
        if np.sum(impacts) == 0:
            raise ValueError("Total impact is zero, cannot perform Pareto analysis")
        
        # Sort items by impact (descending by default)
        sorted_indices = np.argsort(impacts)
        if not ascending:
            sorted_indices = sorted_indices[::-1]
        
        sorted_items = [items[i] for i in sorted_indices]
        sorted_impacts = impacts[sorted_indices]
        
        # Calculate cumulative contribution
        total_impact = np.sum(sorted_impacts)
        cumulative_impacts = np.cumsum(sorted_impacts)
        cumulative_contributions = cumulative_impacts / total_impact
        
        # Find top 20%
        top_20_count = max(1, int(np.ceil(len(items) * 0.20)))
        top_20_indices = list(range(top_20_count))
        top_20_contribution = cumulative_contributions[top_20_count - 1] if top_20_count <= len(cumulative_contributions) else cumulative_contributions[-1]
        
        # Validate Pareto principle
        is_pareto_valid = self.validation_range[0] <= top_20_contribution <= self.validation_range[1]
        
        return ParetoResult(
            top_20_percent_indices=top_20_indices,
            top_20_percent_contribution=float(top_20_contribution),
            cumulative_contributions=cumulative_contributions.tolist(),
            sorted_items=sorted_items,
            total_impact=float(total_impact),
            is_pareto_valid=is_pareto_valid
        )
    
    def get_top_contributors(
        self,
        result: ParetoResult,
        id_field: str = "id",
        impact_field: str = "impact"
    ) -> List[Dict[str, Any]]:
        """
        Extract top contributors from Pareto analysis result.
        
        Args:
            result: ParetoResult from analyze()
            id_field: Field name for identifier
            impact_field: Field name for impact value
        
        Returns:
            List of top contributor dictionaries
        """
        top_items = []
        for idx in result.top_20_percent_indices:
            item = result.sorted_items[idx].copy()
            item['contribution_percent'] = result.cumulative_contributions[idx] * 100
            item['is_top_20'] = True
            top_items.append(item)
        
        return top_items
    
    def analyze_multiple_dimensions(
        self,
        items: List[Dict[str, Any]],
        impact_fields: List[str]
    ) -> Dict[str, ParetoResult]:
        """
        Perform Pareto analysis across multiple impact dimensions.
        
        Args:
            items: List of items to analyze
            impact_fields: List of field names to analyze
        
        Returns:
            Dictionary mapping field names to ParetoResult objects
        """
        results = {}
        for field in impact_fields:
            try:
                results[field] = self.analyze(items, impact_field=field)
            except (ValueError, KeyError) as e:
                # Skip fields that cause errors
                results[field] = None
        
        return results
