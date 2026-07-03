"""Pydantic models for the shared AI service layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """Input payload for text generation requests."""

    system_prompt: str = Field(..., min_length=1)
    user_prompt: str = Field(..., min_length=1)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=1024, ge=1, le=8192)


class AIResponse(BaseModel):
    """Structured response produced by the AI provider."""

    text: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    finish_reason: str = Field(default="unknown", min_length=1)


class AIHealthStatus(BaseModel):
    """Service configuration health for AI endpoints."""

    configured: bool
    model: str
    status: str
