"""SQLAlchemy models — importar todos para que Alembic los descubra."""

from src.infrastructure.database.models.audit import AuditLog, PipelineRun, SecurityEvent, SecurityEventType
from src.infrastructure.database.models.base import Base, TimestampMixin
from src.infrastructure.database.models.conversation import Conversation, Message
from src.infrastructure.database.models.document import AreaFuncional, Document, DocumentChunk
from src.infrastructure.database.models.episodic_memory import EpisodicMemory
from src.infrastructure.database.models.evaluation import RagasEvaluation
from src.infrastructure.database.models.feedback import Feedback
from src.infrastructure.database.models.permission import DTree, DTreeACL, DTreeAncestors, Kuaf, KuafChildren
from src.infrastructure.database.models.user import RefreshToken, User

__all__ = [
    "AreaFuncional",
    "AuditLog",
    "Base",
    "Conversation",
    "DTree",
    "DTreeACL",
    "DTreeAncestors",
    "Document",
    "DocumentChunk",
    "EpisodicMemory",
    "Feedback",
    "Kuaf",
    "KuafChildren",
    "Message",
    "PipelineRun",
    "RagasEvaluation",
    "RefreshToken",
    "SecurityEvent",
    "SecurityEventType",
    "TimestampMixin",
    "User",
]
