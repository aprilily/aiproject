from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from src.search import get_answer_with_sources

app = FastAPI(title="청년 맞춤형 세무 지식 서비스 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # LLM 답변과 출처 JSON을 동시에 받아옴
        result = get_answer_with_sources(request.query)
        
        return {
            "status": "success",
            "query": request.query,
            "answer": result["answer"],
            "sources": result["sources"] # 출처 데이터 추가
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }