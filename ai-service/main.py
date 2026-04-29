from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from data_generator import generate_matches
from recommender import Recommender

recommender: Recommender | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender
    matches = generate_matches(300)
    recommender = Recommender(matches)
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
    return {"status": "ok"}


@app.post("/recommend/matches", response_model=RecommendResponse)
def recommend_matches(user: UserProfile):
    if recommender is None:
        return RecommendResponse(matchIds=[])
    ids = recommender.recommend(user.preferredPosition, user.gender, user.grade)
    return RecommendResponse(matchIds=ids)
