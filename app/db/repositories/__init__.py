"""Repository modules for persistence access."""

from app.db.repositories.claims import ClaimRepository
from app.db.repositories.documents import DocumentRepository
from app.db.repositories.jobs import JobRepository
from app.db.repositories.scores import ScoreRepository

__all__ = [
    "ClaimRepository",
    "DocumentRepository",
    "JobRepository",
    "ScoreRepository",
]
