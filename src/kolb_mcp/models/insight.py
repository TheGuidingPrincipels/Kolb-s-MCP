"""Pydantic models for Insight entities."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class InsightCreate(BaseModel):
    """Model for creating an insight."""

    description: str = Field(..., min_length=20, max_length=1000, description="Insight description")
    type: str = Field(..., description="Type of insight")
    supporting_patterns: List[str] = Field(default_factory=list, description="Pattern IDs that support this insight")
    supporting_experiments: List[str] = Field(default_factory=list, description="Experiment IDs that support this insight")
    actionable_recommendations: List[str] = Field(default_factory=list, max_items=5, description="Specific actions to take")
    expected_impact: Optional[str] = Field(None, max_length=500, description="Predicted outcome")
    importance_score: int = Field(default=5, ge=1, le=10, description="Importance rating (1-10)")

    @validator('type')
    def validate_type(cls, v):
        valid_types = {'breakthrough', 'connection', 'refinement', 'warning'}
        if v not in valid_types:
            raise ValueError(f"Invalid insight type: {v}. Must be one of {valid_types}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Sleep quality directly predicts next-day procrastination behavior",
                "type": "connection",
                "supporting_patterns": ["pat_2025_01_10_sleep", "pat_2025_01_15_procrastination"],
                "supporting_experiments": ["exp_2025_01_20_health"],
                "actionable_recommendations": [
                    "Prioritize 7+ hours sleep on nights before important work",
                    "Schedule deep work tasks for mornings after good sleep"
                ],
                "expected_impact": "30% reduction in procrastination on well-rested days",
                "importance_score": 8
            }
        }


class InsightResponse(BaseModel):
    """Response model for insight operations."""

    success: bool
    insight_id: Optional[str] = None
    importance: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
