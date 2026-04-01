"""Unit tests for job queue factory."""

import pytest
from app.core.config import clear_settings_cache
from app.workers.queue import DatabaseJobQueue, SqsJobQueue, build_job_queue


@pytest.mark.unit
def test_build_job_queue_database_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("JOB_QUEUE_BACKEND", "database")
    clear_settings_cache()

    class _FakeFactory:
        pass

    q = build_job_queue(_FakeFactory())  # type: ignore[arg-type]
    assert isinstance(q, DatabaseJobQueue)
    clear_settings_cache()


@pytest.mark.unit
def test_build_job_queue_sqs(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings_cache()
    monkeypatch.setenv("JOB_QUEUE_BACKEND", "sqs")
    monkeypatch.setenv("SQS_QUEUE_URL", "https://sqs.example.com/queue")
    clear_settings_cache()

    class _FakeFactory:
        pass

    q = build_job_queue(_FakeFactory())  # type: ignore[arg-type]
    assert isinstance(q, SqsJobQueue)
    clear_settings_cache()
