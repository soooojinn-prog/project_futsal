from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="letsfutsal AI Service")


class UserProfile(BaseModel):
    userId: int
    preferredPosition: str
    gender: str  # "MALE", "FEMALE", "ALL"
    grade: int


@app.get("/health")
def health():
    return {"status": "ok"}
