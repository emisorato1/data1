"""API client for eval runner: authentication, session management, SSE parsing.

Handles the full flow: login via HTTPOnly cookies, create conversation,
send message, and parse SSE stream to accumulate the response.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SSEResponse:
    """Parsed result from an SSE chat stream."""

    content: str = ""
    sources: list[dict[str, str]] = field(default_factory=list)
    message_id: str = ""
    guardrail_blocked: bool = False
    error: str | None = None


class APIClient:
    """Stateful HTTP client that authenticates and sends eval questions."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            follow_redirects=True,
        )

    # ── Auth ──────────────────────────────────────────────────

    def login(self, email: str, password: str) -> None:
        """Authenticate and persist session cookies."""
        resp = self._client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        logger.info("Authenticated as %s", email)

    def refresh_token(self) -> None:
        """Attempt to refresh the access token using the refresh cookie."""
        resp = self._client.post("/api/v1/auth/refresh")
        resp.raise_for_status()
        logger.info("Token refreshed")

    # ── Conversations ─────────────────────────────────────────

    def create_conversation(self) -> str:
        """Create a new conversation, return its ID."""
        resp = self._client.post(
            "/api/v1/conversations",
            json={"title": None},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        conv_id: str = data["id"]
        logger.debug("Created conversation %s", conv_id)
        return conv_id

    # ── Chat + SSE ────────────────────────────────────────────

    def send_message(self, conversation_id: str, message: str) -> SSEResponse:
        """Send a message and parse the SSE stream into an SSEResponse."""
        result = SSEResponse()
        try:
            with self._client.stream(
                "POST",
                f"/api/v1/conversations/{conversation_id}/messages",
                json={"message": message},
            ) as stream:
                stream.raise_for_status()
                result = _parse_sse_stream(stream)
        except httpx.TimeoutException:
            result.error = f"Timeout after {self._timeout}s"
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                self.refresh_token()
                return self.send_message(conversation_id, message)
            result.error = f"HTTP {exc.response.status_code}: {exc.response.text}"
        return result

    # ── Cleanup ───────────────────────────────────────────────

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> APIClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _parse_sse_stream(stream: httpx.Response) -> SSEResponse:
    """Parse SSE events from an httpx streaming response."""
    result = SSEResponse()
    current_event: str | None = None

    for line in stream.iter_lines():
        if line.startswith("event:"):
            current_event = line[len("event:") :].strip()
        elif line.startswith("data:") and current_event is not None:
            raw_data = line[len("data:") :].strip()
            _handle_sse_event(current_event, raw_data, result)
            current_event = None

    return result


def _handle_sse_event(event: str, raw_data: str, result: SSEResponse) -> None:
    """Process a single SSE event."""
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        data = {"content": raw_data}

    if event == "token":
        result.content += data.get("content", "")
    elif event == "done":
        result.sources = data.get("sources", [])
        result.message_id = data.get("message_id", "")
    elif event == "guardrail_blocked":
        result.guardrail_blocked = True
        result.content = data.get("content", "")
    elif event == "error":
        result.error = data.get("message", str(data))
