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
from pose.classifier import PoseClassifier
from pose.extractor import PoseExtractor
from pose.features import FeatureBuilder
from pose.feedback import FeedbackGenerator
from pose.schemas import (
    CLASS_NAMES_KO,
    AngleStats,
    KeyAngles,
    PoseAnalysisResponse,
    TimingMs,
)
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

pose_extractor: PoseExtractor | None = None
pose_features: FeatureBuilder | None = None
pose_classifier: PoseClassifier | None = None
pose_feedback: FeedbackGenerator | None = None

CHROMA_DIR = Path(os.environ.get("RAG_CHROMA_DIR", "data/chroma_db"))
POSE_MODEL_PATH = Path(os.environ.get("POSE_MODEL_PATH", "models/best.joblib"))


def _log_langsmith_status() -> None:
    enabled = os.environ.get("LANGSMITH_TRACING", "").lower() in {"true", "1", "yes"}
    if enabled:
        project = os.environ.get("LANGSMITH_PROJECT", "default")
        print(f"[LangSmith] tracing enabled (project={project})")
    else:
        print("[LangSmith] tracing disabled (set LANGSMITH_TRACING=true to enable)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender, rag_chain, router_classifier

    _log_langsmith_status()
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

        # Pose 분석 (모델 파일 있을 때만 활성)
        global pose_extractor, pose_features, pose_classifier, pose_feedback
        pose_extractor = PoseExtractor(sample_fps=10, max_frames=300)
        pose_features = FeatureBuilder()
        if POSE_MODEL_PATH.exists():
            pose_classifier = PoseClassifier(POSE_MODEL_PATH)
            pose_feedback = FeedbackGenerator(claude_client=claude)
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


import tempfile
import time as _time

import numpy as np
from fastapi import File, UploadFile


def _key_angles_from_landmarks(landmarks_per_frame) -> KeyAngles:
    from pose.features import (
        LEFT_ANKLE,
        LEFT_FOOT,
        LEFT_HIP,
        LEFT_KNEE,
        RIGHT_ANKLE,
        RIGHT_FOOT,
        RIGHT_HIP,
        RIGHT_KNEE,
        _angle,
    )

    triples = {
        "left_knee": (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
        "right_knee": (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
        "left_ankle": (LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT),
        "right_ankle": (RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT),
    }
    stats: dict[str, AngleStats] = {}
    for name, (a, b, c) in triples.items():
        vals = [_angle(lm, a, b, c) for lm in landmarks_per_frame]
        arr = np.array(vals)
        stats[name] = AngleStats(
            mean=float(arr.mean()), min=float(arr.min()), max=float(arr.max())
        )
    return KeyAngles(**stats)


@app.post("/pose/analyze", response_model=PoseAnalysisResponse)
def pose_analyze(file: UploadFile = File(...)):
    if pose_classifier is None or pose_feedback is None:
        raise HTTPException(
            status_code=503, detail="Pose 모델이 로드되지 않았습니다."
        )

    t0 = _time.perf_counter()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(file.file.read())
        tmp_path = f.name

    t_frame_start = _time.perf_counter()
    landmarks_per_frame = pose_extractor.extract_from_video(tmp_path)
    t_frame_end = _time.perf_counter()

    if not landmarks_per_frame:
        raise HTTPException(status_code=400, detail="영상에서 사람이 보이지 않아요.")

    feature_vec = pose_features.build_single(landmarks_per_frame)
    t_features_end = _time.perf_counter()

    pose_class, confidence, probs = pose_classifier.predict(feature_vec)
    t_classify_end = _time.perf_counter()

    key_angles = _key_angles_from_landmarks(landmarks_per_frame)

    t_feedback_start = _time.perf_counter()
    feedback = pose_feedback.generate(pose_class, confidence, key_angles)
    t_feedback_end = _time.perf_counter()

    return PoseAnalysisResponse(
        pose_class=pose_class,
        class_name=CLASS_NAMES_KO.get(pose_class, pose_class),
        confidence=confidence,
        class_probabilities=probs,
        key_angles=key_angles,
        feedback=feedback,
        timing_ms=TimingMs(
            frame_extract=int((t_frame_end - t_frame_start) * 1000),
            mediapipe=int((t_features_end - t_frame_end) * 1000),
            classify=int((t_classify_end - t_features_end) * 1000),
            feedback=int((t_feedback_end - t_feedback_start) * 1000),
            total=int((t_feedback_end - t0) * 1000),
        ),
    )


@app.post("/agent/run", response_model=ProposalResponse)
def agent_run(req: AgentRequest):
    if agent_graph is None:
        raise HTTPException(
            status_code=503, detail="에이전트가 초기화되지 않았습니다."
        )
    state = make_initial_state(
        user_input=req.user_input, user_id=req.user_id, team_info=req.team_info
    )
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
