import pytest
from unittest.mock import AsyncMock, MagicMock, patch


async def test_pipeline_no_queries():
    with patch("app.pipeline.storage.get_active_queries", new_callable=AsyncMock) as mock_q:
        mock_q.return_value = []
        from app.pipeline import run_pipeline
        result = await run_pipeline()
        assert result["status"] == "no_queries"
        assert result["new_jobs"] == 0


async def test_pipeline_no_new_jobs():
    fake_jobs = [{"job_id": "abc123", "title": "Test", "company": "Acme", "score": 80}]

    with (
        patch("app.pipeline.storage.get_active_queries", new_callable=AsyncMock) as mock_q,
        patch("app.pipeline.storage.get_seen_job_ids", new_callable=AsyncMock) as mock_seen,
        patch("app.pipeline.search.search_all_queries", return_value=fake_jobs),
        patch("app.pipeline.storage.save_jobs", new_callable=AsyncMock),
    ):
        mock_q.return_value = ["OneStream Lead Architect"]
        mock_seen.return_value = {"abc123"}

        from app.pipeline import run_pipeline
        result = await run_pipeline()
        assert result["new_jobs"] == 0
        assert result["sent"] == 0


def test_score_badge_in_email():
    from app.emailer import _score_badge
    assert "22c55e" in _score_badge(90)
    assert "f59e0b" in _score_badge(75)
    assert "6b7280" in _score_badge(50)


def test_job_id_is_deterministic():
    from app.search import _make_job_id
    id1 = _make_job_id("Lead Architect", "Acme", "https://example.com/job/1")
    id2 = _make_job_id("Lead Architect", "Acme", "https://example.com/job/1")
    assert id1 == id2
    assert len(id1) == 16
