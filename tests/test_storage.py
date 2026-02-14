# tests/test_storage.py
import tempfile
from pathlib import Path

from ai4news.storage import Database


def make_db() -> Database:
    tmp = tempfile.mktemp(suffix=".db")
    return Database(Path(tmp))


def test_create_tables():
    db = make_db()
    # Should not raise
    db.close()


def test_upsert_target():
    db = make_db()
    tid = db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test User",
    )
    assert tid is not None
    targets = db.list_targets()
    assert len(targets) == 1
    assert targets[0]["name"] == "Test User"
    db.close()


def test_upsert_target_dedup():
    db = make_db()
    tid1 = db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test User",
    )
    tid2 = db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test User Updated",
    )
    assert tid1 == tid2
    targets = db.list_targets()
    assert len(targets) == 1
    assert targets[0]["name"] == "Test User Updated"
    db.close()


def test_remove_target():
    db = make_db()
    db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test User",
    )
    removed = db.remove_target("https://www.linkedin.com/in/test")
    assert removed is True
    assert db.list_targets() == []
    db.close()


def test_insert_post_and_dedup():
    db = make_db()
    tid = db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test",
    )
    inserted = db.insert_post(
        target_id=tid,
        linkedin_id="urn:li:activity:123",
        author="Test",
        text="Hello world",
        url="https://linkedin.com/feed/update/urn:li:activity:123",
        media_urls=[],
        posted_at="2026-02-14T10:00:00",
    )
    assert inserted is True

    # Same linkedin_id should be skipped
    inserted2 = db.insert_post(
        target_id=tid,
        linkedin_id="urn:li:activity:123",
        author="Test",
        text="Duplicate",
        url="https://linkedin.com/feed/update/urn:li:activity:123",
        media_urls=[],
        posted_at="2026-02-14T10:00:00",
    )
    assert inserted2 is False
    db.close()


def test_get_new_posts():
    db = make_db()
    tid = db.upsert_target(
        url="https://www.linkedin.com/in/test",
        target_type="person",
        name="Test",
    )
    db.insert_post(
        target_id=tid,
        linkedin_id="urn:li:activity:001",
        author="Test",
        text="Post one",
        url="https://linkedin.com/feed/update/urn:li:activity:001",
        media_urls=["https://img.com/1.jpg"],
        posted_at="2026-02-14T10:00:00",
    )
    posts = db.get_new_posts(since_days=7)
    assert len(posts) == 1
    assert posts[0]["text"] == "Post one"
    assert posts[0]["author"] == "Test"
    assert posts[0]["media_urls"] == ["https://img.com/1.jpg"]
    db.close()


def test_record_newsletter():
    db = make_db()
    db.record_newsletter(file_path="/tmp/test.html", post_count=5)
    db.close()
