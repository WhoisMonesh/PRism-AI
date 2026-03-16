import pytest
from unittest.mock import MagicMock, AsyncMock
from src.review_engine import ReviewEngine, ReviewResult, ReviewComment

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = '{"summary": "Test summary", "score": 85, "approved": true, "comments": []}'
    return llm

@pytest.fixture
def engine_config():
    return {
        "llm": {"provider": "ollama"},
        "policy": {"rbac_enabled": False}
    }

@pytest.mark.asyncio
async def test_review_engine_success(mock_llm, engine_config, monkeypatch):
    # Mock create_llm_client to return our mock_llm
    monkeypatch.setattr("src.review_engine.create_llm_client", lambda x: mock_llm)
    
    engine = ReviewEngine(engine_config)
    result = await engine.review_pr(
        pr_number=1,
        repo="owner/repo",
        diff="--- a/file.py\n+++ b/file.py\n+print('hello')",
        pr_title="Add hello print",
        pr_body="Adds a hello world print statement",
        changed_files=["file.py"]
    )
    
    assert isinstance(result, ReviewResult)
    assert result.score == 85
    assert result.approved is True
    assert result.summary == "Test summary"
    mock_llm.generate.assert_called_once()
