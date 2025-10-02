"""Pydantic models for Experiment entities."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date


class ExperimentCreate(BaseModel):
    """Model for creating a new experiment."""

    domain: str = Field(..., description="Life domain for experiment")
    hypothesis: str = Field(..., min_length=20, max_length=500, description="What you expect to happen")
    intervention: str = Field(..., min_length=10, max_length=500, description="Specific change to make")
    primary_metrics: List[str] = Field(..., min_items=1, max_items=5, description="Main success indicators")
    guardrail_metrics: List[str] = Field(default_factory=list, max_items=3, description="Safety metrics to monitor")
    duration_days: int = Field(default=7, ge=1, le=90, description="Experiment duration")
    target_pattern_id: Optional[str] = Field(None, description="Pattern this experiment targets")

    @validator('domain')
    def validate_domain(cls, v):
        valid_domains = {'work', 'health', 'relationships', 'learning', 'personal'}
        if v not in valid_domains:
            raise ValueError(f"Invalid domain: {v}. Must be one of {valid_domains}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "work",
                "hypothesis": "Working in 90-minute focused blocks will increase deep work completion by 30%",
                "intervention": "Set timer for 90 min, disable all notifications, close email/slack",
                "primary_metrics": ["deep work hours completed", "task completion rate"],
                "guardrail_metrics": ["stress level", "energy at end of day"],
                "duration_days": 7,
                "target_pattern_id": "pat_2025_01_15_abc123"
            }
        }


class ObservationCreate(BaseModel):
    """Model for recording daily experiment observation."""

    experiment_id: str = Field(..., description="Experiment being tracked")
    observation: str = Field(..., min_length=10, max_length=1000, description="What happened today")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metric values for today")
    energy_level: int = Field(..., ge=1, le=10, description="Energy level (1-10)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "experiment_id": "exp_2025_01_15_wor",
                "observation": "Completed 2 focused blocks, felt much more productive than usual",
                "metrics": {
                    "deep_work_hours": 3.0,
                    "tasks_completed": 5,
                    "stress_level": 3
                },
                "energy_level": 7,
                "notes": "Morning block was best, afternoon harder to maintain focus"
            }
        }


class ExperimentResponse(BaseModel):
    """Response model for experiment operations."""

    success: bool
    experiment_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    days_remaining: Optional[int] = None
    current_day: Optional[int] = None


class ExperimentRecommendation(BaseModel):
    """Model for experiment recommendation."""

    type: str = Field(..., description="Recommendation type")
    domain: str = Field(..., description="Target domain")
    hypothesis: str = Field(..., description="Suggested hypothesis")
    intervention: str = Field(..., description="Suggested intervention")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated success probability")
    reasoning: str = Field(..., description="Why this experiment is recommended")
    target_pattern_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "type": "pattern_intervention",
                "domain": "work",
                "hypothesis": "Breaking down large tasks into 25-min segments will reduce procrastination",
                "intervention": "Use Pomodoro technique for all tasks estimated >1 hour",
                "success_probability": 0.7,
                "reasoning": "Targets high-confidence procrastination pattern",
                "target_pattern_id": "pat_2025_01_15_abc123"
            }
        }
