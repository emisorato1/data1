from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    user_role: str = "public"
    message: str

class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: list = []
    rag: dict | None = None
