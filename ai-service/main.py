import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

from data_generator import generate_matches
from agent.graph import build_agent_graph
from agent.schemas import (
    AgentRequest,
    BracketDTO,
    MatchProposal,
    ProposalResponse,
    TeamSummary,
)
from agent.springboot_client import SpringbootClient
from agent.state import make_initial_state
from agent.tools import Tools
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
agent_graph = None

CHROMA_DIR = Path(os.environ.get("RAG_CHROMA_DIR", "data/chroma_db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender, rag_chain, router_classifier

    matches = generate_matches(300)
    recommender = Recommender(matches)

    global agent_graph
    if CHROMA_DIR.exists():
        retriever = open_persistent_retriever(CHROMA_DIR)
        claude = ClaudeClient()
        rag_chain = RagChain(retriever=retriever, claude_client=claude)
        router_classifier = RouterClassifier(claude_client=claude)

        # 에이전트 그래프 (RAG와 같은 Claude 클라이언트 재사용)
        spring_client = SpringbootClient()
        agent_tools = Tools(client=spring_client)
        agent_graph = build_agent_graph(claude_client=claude, tools=agent_tools)
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


def _match_dict_to_proposal(m: dict) -> MatchProposal:
    def _team(t: dict | None) -> TeamSummary | None:
        if t is None:
            return None
        return TeamSummary(id=t.get("id"), name=t.get("name") or "팀")

    return MatchProposal(
        stadium_id=m["stadium_id"],
        stadium_name=m["stadium_name"],
        start_time=m["start_time"],
        duration_min=m.get("duration_min", 60),
        team_a=_team(m.get("team_a")) or TeamSummary(name="내 팀"),
        team_b=_team(m.get("team_b")),
        stage=m.get("stage"),
    )


@app.post("/agent/run", response_model=ProposalResponse)
def agent_run(req: AgentRequest):
    if agent_graph is None:
        raise HTTPException(
            status_code=503, detail="에이전트가 초기화되지 않았습니다."
        )
    state = make_initial_state(user_input=req.user_input, user_id=req.user_id)
    final = agent_graph.invoke(state)

    matches = [_match_dict_to_proposal(m) for m in final.get("proposals", [])]
    bracket = (
        BracketDTO(rounds=final["bracket"]["rounds"]) if final.get("bracket") else None
    )
    return ProposalResponse(
        proposal_id=final.get("proposal_id", "prop_unknown"),
        intent=final.get("intent", "UNKNOWN"),
        warnings=final.get("warnings", []),
        matches=matches,
        bracket=bracket,
    )
