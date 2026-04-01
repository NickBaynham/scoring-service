"""Initial schema for documents, jobs, scores, spans, claims."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20250331000000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("text_uri", sa.String(length=2048), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("profile", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_tenant_id"), "documents", ["tenant_id"], unique=False)

    op.create_table(
        "score_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("profile_name", sa.String(length=64), nullable=False),
        sa.Column("profile_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_score_jobs_document_id"), "score_jobs", ["document_id"], unique=False)
    op.create_index(op.f("ix_score_jobs_tenant_id"), "score_jobs", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_score_jobs_status"), "score_jobs", ["status"], unique=False)

    op.create_table(
        "score_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("score_name", sa.String(length=64), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rationale_json", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["score_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_score_results_document_id"), "score_results", ["document_id"], unique=False)
    op.create_index(op.f("ix_score_results_job_id"), "score_results", ["job_id"], unique=False)
    op.create_index(op.f("ix_score_results_score_name"), "score_results", ["score_name"], unique=False)

    op.create_table(
        "score_spans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("score_result_id", sa.String(length=36), nullable=False),
        sa.Column("quoted_span", sa.Text(), nullable=False),
        sa.Column("issue_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["score_result_id"], ["score_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_score_spans_score_result_id"), "score_spans", ["score_result_id"], unique=False)

    op.create_table(
        "claims",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=64), nullable=False),
        sa.Column("source_chunk", sa.Text(), nullable=True),
        sa.Column("normalized_form", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_claims_document_id"), "claims", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_claims_document_id"), table_name="claims")
    op.drop_table("claims")
    op.drop_index(op.f("ix_score_spans_score_result_id"), table_name="score_spans")
    op.drop_table("score_spans")
    op.drop_index(op.f("ix_score_results_score_name"), table_name="score_results")
    op.drop_index(op.f("ix_score_results_job_id"), table_name="score_results")
    op.drop_index(op.f("ix_score_results_document_id"), table_name="score_results")
    op.drop_table("score_results")
    op.drop_index(op.f("ix_score_jobs_status"), table_name="score_jobs")
    op.drop_index(op.f("ix_score_jobs_tenant_id"), table_name="score_jobs")
    op.drop_index(op.f("ix_score_jobs_document_id"), table_name="score_jobs")
    op.drop_table("score_jobs")
    op.drop_index(op.f("ix_documents_tenant_id"), table_name="documents")
    op.drop_table("documents")
