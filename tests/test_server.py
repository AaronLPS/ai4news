# tests/test_server.py
"""Tests for MCP server: _build_activity_url, store_posts, and tool registration."""
import pytest

from ai4news.server import mcp, _build_activity_url, store_posts, _get_db
from ai4news.config import get_data_dir


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Provide a fresh in-memory-like DB using a temp directory."""
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("ai4news.config.get_data_dir", lambda: tmp_path)
    database = _get_db()
    yield database
    database.close()


# --- _build_activity_url tests ---


def test_build_activity_url_person():
    url = _build_activity_url("https://www.linkedin.com/in/satyanadella", "person")
    assert url == "https://www.linkedin.com/in/satyanadella/recent-activity/all/"


def test_build_activity_url_company():
    url = _build_activity_url("https://www.linkedin.com/company/openai", "company")
    assert url == "https://www.linkedin.com/company/openai/posts/"


def test_build_activity_url_hashtag():
    url = _build_activity_url("https://www.linkedin.com/feed/hashtag/ai", "hashtag")
    assert url == "https://www.linkedin.com/feed/hashtag/ai"


def test_build_activity_url_strips_trailing_slash():
    url = _build_activity_url("https://www.linkedin.com/in/satyanadella/", "person")
    assert url == "https://www.linkedin.com/in/satyanadella/recent-activity/all/"


# --- store_posts tests ---


def test_store_posts_new_posts(db, monkeypatch):
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: db.db_path.parent)
    target_url = "https://www.linkedin.com/in/testuser"
    db.upsert_target(url=target_url, target_type="person", name="Test User")

    posts = [
        {"linkedin_id": "urn:li:activity:111", "author": "Alice", "text": "Hello"},
        {"linkedin_id": "urn:li:activity:222", "author": "Bob", "text": "World"},
    ]
    result = store_posts(target_url, posts)
    assert result["stored"] == 2
    assert result["new"] == 2
    assert result["duplicates"] == 0
    assert result["errors"] == []


def test_store_posts_dedup(db, monkeypatch):
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: db.db_path.parent)
    target_url = "https://www.linkedin.com/in/testuser"
    db.upsert_target(url=target_url, target_type="person", name="Test User")

    posts = [{"linkedin_id": "urn:li:activity:111", "author": "Alice", "text": "Hello"}]
    store_posts(target_url, posts)
    # Store same post again
    result = store_posts(target_url, posts)
    assert result["stored"] == 1
    assert result["new"] == 0
    assert result["duplicates"] == 1


def test_store_posts_unknown_target(db, monkeypatch):
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: db.db_path.parent)
    result = store_posts("https://www.linkedin.com/in/nobody", [])
    assert "error" in result


def test_store_posts_trailing_slash_normalization(db, monkeypatch):
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: db.db_path.parent)
    target_url = "https://www.linkedin.com/in/testuser"
    db.upsert_target(url=target_url, target_type="person", name="Test User")

    posts = [{"linkedin_id": "urn:li:activity:333", "author": "Alice", "text": "Hi"}]
    # Call with trailing slash -- should still match
    result = store_posts(target_url + "/", posts)
    assert result["new"] == 1


def test_store_posts_missing_linkedin_id(db, monkeypatch):
    monkeypatch.setattr("ai4news.server.get_data_dir", lambda: db.db_path.parent)
    target_url = "https://www.linkedin.com/in/testuser"
    db.upsert_target(url=target_url, target_type="person", name="Test User")

    posts = [{"author": "Alice", "text": "No ID here"}]
    result = store_posts(target_url, posts)
    assert result["stored"] == 0
    assert len(result["errors"]) == 1
    assert "missing linkedin_id" in result["errors"][0]


# --- Tool registration test ---


def test_server_has_expected_tools():
    assert mcp is not None
    assert mcp.name == "ai4news"
