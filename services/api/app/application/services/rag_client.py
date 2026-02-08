# app/services/rag_client.py
import httpx
from app.core.config import settings
from langfuse import observe
from app.infrastructure.http.langfuse_client import get_current_trace_id

class RagClient:
    def __init__(self) -> None:
        self.base_url = settings.RAG_BASE_URL.rstrip("/")
        self.assistant_id = settings.RAG_ASSISTANT_ID
        self.timeout = settings.RAG_TIMEOUT_SECONDS

    async def run_and_join(self, *, message: str, session_id: str, user_role: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/runs",
                json={
                    "assistant_id": self.assistant_id,
                    "input": {"message": message, "session_id": session_id, "user_role": user_role},
                    "on_completion": "keep",
                },
            )
            r.raise_for_status()
            run = r.json()

            j = await client.get(
                f"{self.base_url}/threads/{run['thread_id']}/runs/{run['run_id']}/join"
            )
            j.raise_for_status()
            return j.json()


    @observe(name="rag_run", capture_input=True, capture_output=True)
    async def run(
        self, *, message: str, session_id: str, user_role: str, trace_id: str | None = None
    ) -> dict:
         async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Propagar trace_id al servicio RAG
            headers = {}
            effective_trace_id = trace_id or get_current_trace_id()
            if effective_trace_id:
                headers["X-Langfuse-Trace-Id"] = effective_trace_id

            # 1. Crear thread
            thread_response = await client.post(
                f"{self.base_url}/threads",
                json={"thread_id": thread_id, "metadata": {"user_role": user_role}},
                headers=headers,
            )