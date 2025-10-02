"""Pydantic models for Pattern entities."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PatternCreate(BaseModel):
    """Model for creating a new behavioral pattern."""

    description: str = Field(..., min_length=10, max_length=1000, description="Clear pattern description")
    pattern_type: str = Field(..., description="Type of pattern")
    domains: List[str] = Field(..., min_items=1, max_items=5, description="Affected life domains")
    triggers: List[str] = Field(default_factory=list, description="Pattern triggers")
    frequency: str = Field(default="situational", description="How often pattern occurs")
    confidence: float = Field(default=0.3, ge=0.0, le=1.0, description="Initial confidence score")

    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        valid_types = {'behavioral', 'cognitive', 'emotional', 'systemic', 'temporal'}
        if v not in valid_types:
            raise ValueError(f"Invalid pattern_type: {v}. Must be one of {valid_types}")
        return v

    @validator('domains')
    def validate_domains(cls, v):
        valid_domains = {'work', 'health', 'relationships', 'learning', 'personal'}
        for domain in v:
            if domain not in valid_domains:
                raise ValueError(f"Invalid domain: {domain}. Must be one of {valid_domains}")
        return v

    @validator('frequency')
    def validate_frequency(cls, v):
        valid_frequencies = {'daily', 'weekly', 'situational', 'triggered'}
        if v not in valid_frequencies:
            raise ValueError(f"Invalid frequency: {v}. Must be one of {valid_frequencies}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Procrastinate on tasks requiring >2 hours of uninterrupted focus",
                "pattern_type": "behavioral",
                "domains": ["work"],
                "triggers": ["complex tasks", "uncertainty", "fatigue"],
                "frequency": "daily",
                "confidence": 0.3
            }
        }


class PatternUpdate(BaseModel):
    """Model for updating pattern confidence."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    new_confidence: float = Field(..., ge=0.0, le=1.0, description="Updated confidence score")
    evidence: str = Field(..., min_length=10, max_length=500, description="Evidence for confidence change")

    class Config:
        json_schema_extra = {
            "example": {
                "pattern_id": "pat_2025_01_15_abc123",
                "new_confidence": 0.6,
                "evidence": "Pattern repeated 3 times this week with same triggers"
            }
        }


class PatternResponse(BaseModel):
    """Response model for pattern operations."""

    success: bool
    pattern_id: Optional[str] = None
    confidence: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None
    related_patterns: Optional[List[str]] = None


class PatternQuery(BaseModel):
    """Model for querying patterns."""

    domain: Optional[str] = None
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    pattern_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)

    @validator('domain')
    def validate_domain(cls, v):
        if v is None:
            return v
        valid_domains = {'work', 'health', 'relationships', 'learning', 'personal'}
        if v not in valid_domains:
            raise ValueError(f"Invalid domain: {v}")
        return v
