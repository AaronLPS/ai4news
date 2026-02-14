# tests/test_integration.py
"""End-to-end test: config -> storage -> newsletter (without Playwright)."""
import tempfile
from pathlib import Path

from ai4news.config import load_targets, save_targets
from ai4news.storage import Database
from ai4news.newsletter import generate_html


def test_full_pipeline_without_scraping():
    """Simulate the full pipeline: load config, store posts, generate newsletter."""
    # 1. Create temp config
    config_path = Path(tempfile.mktemp(suffix=".yaml"))
    save_targets(
        [
            {"type": "person", "name": "Test User", "url": "https://www.linkedin.com/in/testuser"},
            {"type": "company", "name": "Test Co", "url": "https://www.linkedin.com/company/testco"},
        ],
        config_path,
    )

    # 2. Load config
    targets = load_targets(config_path)
    assert len(targets) == 2

    # 3. Store in DB
    db = Database(Path(tempfile.mktemp(suffix=".db")))
    tid1 = db.upsert_target(url=targets[0]["url"], target_type=targets[0]["type"], name=targets[0]["name"])
    tid2 = db.upsert_target(url=targets[1]["url"], target_type=targets[1]["type"], name=targets[1]["name"])

    db.insert_post(
        target_id=tid1, linkedin_id="urn:li:activity:001", author="Test User",
        text="Hello from person", url="https://linkedin.com/feed/update/urn:li:activity:001",
        media_urls=[], posted_at="2026-02-14T10:00:00",
    )
    db.insert_post(
        target_id=tid2, linkedin_id="urn:li:activity:002", author="Test Co",
        text="Hello from company", url="https://linkedin.com/feed/update/urn:li:activity:002",
        media_urls=["https://img.com/logo.png"], posted_at="2026-02-13T10:00:00",
    )

    # 4. Query new posts
    posts = db.get_new_posts(since_days=7)
    assert len(posts) == 2

    # 5. Simulate AI summaries (what Claude would do)
    for post in posts:
        post["summary"] = f"Summary of: {post['text'][:30]}"

    # 6. Generate newsletter
    output_dir = Path(tempfile.mkdtemp())
    html_path = generate_html(posts, output_dir)
    assert html_path.exists()

    html = html_path.read_text()
    assert "Test User" in html
    assert "Test Co" in html
    assert "Summary of:" in html
    assert "View original" in html

    db.close()
