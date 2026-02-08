# /app/infrastructure/http/rag_client.py
from __future__ import annotations

import httpx
import json
from uuid import UUID
from app.core.config import settings


class RagClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.RAG_BASE_URL).rstrip("/")
        self.assistant_id = settings.RAG_ASSISTANT_ID
        self.timeout = settings.RAG_TIMEOUT_SECONDS

    async def run(
        self, 
        *, 
        message: str, 
        session_id: str, 
        user_id: UUID, 
        tenant_id: UUID,
        user_role: str = "user",
    ) -> dict:
        """
        Ejecuta el grafo de LangGraph y espera el resultado.
        
        LangGraph API requiere:
        1. POST /threads para crear el thread (si no existe)
        2. POST /threads/{thread_id}/runs para crear un run
        3. GET /threads/{thread_id}/runs/{run_id}/join para esperar el resultado
        
        Args:
            message: Mensaje del usuario
            session_id: ID de la sesión/thread
            user_id: ID del usuario autenticado
            tenant_id: ID del tenant del usuario
            user_role: Rol del usuario (para permisos de documentos)
        
        Returns:
            Estado final del grafo con campos: response, sources, session_id, etc.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            thread_id = session_id
            
            # 1. Intentar crear el thread (ignorar si ya existe)
            thread_response = await client.post(
                f"{self.base_url}/threads",
                json={
                    "thread_id": thread_id, 
                    "metadata": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                    },
                    "if_exists": "do_nothing",
                },
            )
            # 409 = thread ya existe, está bien
            # 200/201 = thread creado
            if thread_response.status_code not in (200, 201, 409):
                thread_response.raise_for_status()
            
            # 2. Ejecutar el grafo con contexto de usuario
            # El input debe coincidir con RAGState: message, session_id, user_role
            run_response = await client.post(
                f"{self.base_url}/threads/{thread_id}/runs",
                json={
                    "assistant_id": self.assistant_id,
                    "input": {
                        "message": message,
                        "session_id": session_id,
                        "user_role": user_role,
                    },
                    "config": {
                        "configurable": {
                            "tenant_id": str(tenant_id),
                            "user_id": str(user_id),
                            "user_role": user_role,
                        }
                    },
                    "metadata": {
                        "source": "api-gateway",
                    },
                },
            )
            run_response.raise_for_status()
            run = run_response.json()
            run_id = run.get("run_id")

            # 3. Esperar a que termine el run
            join_response = await client.get(
                f"{self.base_url}/threads/{thread_id}/runs/{run_id}/join"
            )
            join_response.raise_for_status()
            return join_response.json()

    # Alias para compatibilidad
    run_and_join = run

    async def stream(
        self,
        *,
        message: str,
        session_id: str,
        user_id: UUID,
        tenant_id: UUID,
        user_role: str,
    ):
        """
        Ejecuta el grafo modo streaming (server-sent events).
        
        Args:
            message: Mensaje del usuario
            session_id: ID de la sesión/thread (short-term memory)
            user_id: ID del usuario autenticado (long-term memory)
            tenant_id: ID del tenant del usuario
            user_role: Rol del usuario (para permisos de documentos)
            
        Yields:
            dict: Evento parseado con keys 'event' y 'data' (dict)
        """
        thread_id = session_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Asegurar thread con metadata del usuario
            await client.post(
                f"{self.base_url}/threads",
                json={
                    "thread_id": thread_id,
                    "metadata": {
                        "tenant_id": str(tenant_id),
                        "user_id": str(user_id),
                        "user_role": user_role,
                    },
                    "if_exists": "do_nothing",
                },
            )
            
            # 2. Hacer el stream con config que incluye user_id para long-term memory
            async with client.stream(
                "POST", 
                f"{self.base_url}/threads/{thread_id}/runs/stream",
                json={
                    "assistant_id": self.assistant_id,
                    "input": {
                        "message": message,
                        "session_id": session_id,
                        "user_role": user_role,
                    },
                    "config": {
                        "configurable": {
                            "tenant_id": str(tenant_id),
                            "user_id": str(user_id),
                            "user_role": user_role,
                        }
                    },
                    "stream_mode": "events",
                    "metadata": {
                        "source": "api-gateway-stream",
                    },
                }
            ) as response:
                response.raise_for_status()
                
                # Procesamiento basico de SSE
                current_event = "message"
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("event: "):
                        current_event = line[7:]
                        continue
                        
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            # Parsear data como JSON
                            data_json = json.loads(data_str)
                            
                            yield {
                                "event": current_event, 
                                "data": data_json
                            }
                        except:
                            pass
