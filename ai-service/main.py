import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from data_generator import generate_matches
from rag.chain import RagChain
from rag.claude_client import ClaudeClient
from rag.retriever import open_persistent_retriever
from rag.router_classifier import RouterClassifier
from rag.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    RagRequest,
    RagResponse,
)
from recommender import Recommender

recommender: Recommender | None = None
rag_chain: RagChain | None = None
router_classifier: RouterClassifier | None = None

CHROMA_DIR = Path(os.environ.get("RAG_CHROMA_DIR", "data/chroma_db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender, rag_chain, router_classifier

    matches = generate_matches(300)
    recommender = Recommender(matches)

    if CHROMA_DIR.exists():
        retriever = open_persistent_retriever(CHROMA_DIR)
        claude = ClaudeClient()
        rag_chain = RagChain(retriever=retriever, claude_client=claude)
        router_classifier = RouterClassifier(claude_client=claude)
    yield


app = FastAPI(title="letsfutsal AI Service", lifespan=lifespan)


class UserProfile(BaseModel):
    userId: int
    preferredPosition: str
    gender: str  # "MALE", "FEMALE", "ALL"
    grade: int


class RecommendResponse(BaseModel):
    matchIds: list[int]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rag_enabled": rag_chain is not None,
    }


@app.post("/recommend/matches", response_model=RecommendResponse)
def recommend_matches(user: UserProfile):
    if recommender is None:
        return RecommendResponse(matchIds=[])
    ids = recommender.recommend(user.preferredPosition, user.gender, user.grade)
    return RecommendResponse(matchIds=ids)


@app.post("/chat/rag", response_model=RagResponse)
def chat_rag(req: RagRequest):
    if rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="RAG가 초기화되지 않았습니다. build_index를 먼저 실행하세요.",
        )
    return rag_chain.answer(req.user_message, user_context=req.user_context)


@app.post("/router/classify", response_model=ClassifyResponse)
def router_classify(req: ClassifyRequest):
    if router_classifier is None:
        raise HTTPException(
            status_code=503, detail="라우터 분류기가 초기화되지 않았습니다."
        )
    return router_classifier.classify(req.user_message)
