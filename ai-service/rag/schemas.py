from typing import Literal

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    nickname: str | None = None
    grade: str | None = None
    preferred_position: str | None = None


class Citation(BaseModel):
    source: str
    section: str
    page: int | None = None
    snippet: str
    score: float


class RagRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=500)
    user_context: UserContext | None = None


class RagResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    retrieved_chunks: int = 0


class ClassifyRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=500)


class ClassifyResponse(BaseModel):
    intent: Literal["KNOWLEDGE", "ADVICE"]
    confidence: float = Field(ge=0.0, le=1.0)
