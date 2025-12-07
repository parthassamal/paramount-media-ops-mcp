"""Pareto Analysis Engine - 80/20 rule implementation"""
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np


class ParetoAnalyzer:
    """Analyzes data using Pareto principle (80/20 rule)"""
    
    @staticmethod
    def analyze(data: List[Dict[str, Any]], value_key: str, label_key: str) -> Dict[str, Any]:
        """
        Perform Pareto analysis on data
        
        Args:
            data: List of dictionaries containing the data
            value_key: Key for the numeric value to analyze
            label_key: Key for the label/category
            
        Returns:
            Dictionary with Pareto analysis results
        """
        if not data:
            return {
                "total_items": 0,
                "vital_few": [],
                "vital_few_count": 0,
                "vital_few_percentage": 0,
                "vital_few_contribution": 0,
                "cumulative_data": []
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Sort by value in descending order
        df_sorted = df.sort_values(by=value_key, ascending=False).reset_index(drop=True)
        
        # Calculate cumulative sum and percentage
        total = df_sorted[value_key].sum()
        df_sorted['cumulative_value'] = df_sorted[value_key].cumsum()
        df_sorted['cumulative_percentage'] = (df_sorted['cumulative_value'] / total * 100).round(2)
        df_sorted['contribution_percentage'] = (df_sorted[value_key] / total * 100).round(2)
        
        # Identify vital few (items contributing to ~80% of impact)
        vital_few_mask = df_sorted['cumulative_percentage'] <= 80
        vital_few = df_sorted[vital_few_mask]
        
        # If no items reach 80%, include the first item that crosses 80%
        if len(vital_few) == 0 or df_sorted.loc[len(vital_few) - 1, 'cumulative_percentage'] < 80:
            if len(df_sorted) > len(vital_few):
                vital_few = df_sorted.iloc[:len(vital_few) + 1]
        
        return {
            "total_items": len(df_sorted),
            "total_value": float(total),
            "vital_few": vital_few[[label_key, value_key, 'contribution_percentage', 'cumulative_percentage']].to_dict('records'),
            "vital_few_count": len(vital_few),
            "vital_few_percentage": round(len(vital_few) / len(df_sorted) * 100, 2) if len(df_sorted) > 0 else 0,
            "vital_few_contribution": float(vital_few['cumulative_value'].iloc[-1]) if len(vital_few) > 0 else 0,
            "cumulative_data": df_sorted[[label_key, value_key, 'cumulative_percentage']].to_dict('records'),
            "pareto_insight": f"{len(vital_few)} items ({round(len(vital_few) / len(df_sorted) * 100, 1)}%) contribute to {round(vital_few['cumulative_percentage'].iloc[-1] if len(vital_few) > 0 else 0, 1)}% of total impact"
        }
    
    @staticmethod
    def identify_critical_issues(issues: List[Dict[str, Any]], impact_key: str = "impact_score") -> List[Dict[str, Any]]:
        """Identify critical issues using Pareto principle"""
        result = ParetoAnalyzer.analyze(issues, impact_key, "issue_id")
        return result["vital_few"]
