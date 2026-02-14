# tests/test_newsletter.py
import tempfile
from pathlib import Path

from ai4news.newsletter import generate_html, group_posts_by_target


SAMPLE_POSTS = [
    {
        "author": "Satya Nadella",
        "target_name": "Satya Nadella",
        "target_type": "person",
        "text": "Excited about the future of AI.",
        "summary": "Nadella shares optimism about AI's transformative potential.",
        "url": "https://linkedin.com/feed/update/urn:li:activity:001",
        "media_urls": [],
        "posted_at": "2026-02-14T10:00:00",
    },
    {
        "author": "Satya Nadella",
        "target_name": "Satya Nadella",
        "target_type": "person",
        "text": "Great progress on Copilot.",
        "summary": "Update on Microsoft Copilot development milestones.",
        "url": "https://linkedin.com/feed/update/urn:li:activity:002",
        "media_urls": ["https://img.com/1.jpg"],
        "posted_at": "2026-02-12T10:00:00",
    },
    {
        "author": "OpenAI",
        "target_name": "OpenAI",
        "target_type": "company",
        "text": "We are hiring engineers.",
        "summary": "OpenAI announces engineering hiring initiative.",
        "url": "https://linkedin.com/feed/update/urn:li:activity:003",
        "media_urls": [],
        "posted_at": "2026-02-13T10:00:00",
    },
]


def test_group_posts_by_target():
    groups = group_posts_by_target(SAMPLE_POSTS)
    assert len(groups) == 2
    names = [g["target_name"] for g in groups]
    assert "Satya Nadella" in names
    assert "OpenAI" in names
    for g in groups:
        if g["target_name"] == "Satya Nadella":
            assert len(g["posts"]) == 2


def test_generate_html_contains_key_elements():
    output_dir = Path(tempfile.mkdtemp())
    path = generate_html(SAMPLE_POSTS, output_dir)
    assert path.exists()
    html = path.read_text()
    assert "AI4News Weekly" in html
    assert "Satya Nadella" in html
    assert "OpenAI" in html
    assert "Nadella shares optimism" in html
    assert "View original" in html
    assert "https://linkedin.com/feed/update/urn:li:activity:001" in html


def test_generate_html_is_self_contained():
    output_dir = Path(tempfile.mkdtemp())
    path = generate_html(SAMPLE_POSTS, output_dir)
    html = path.read_text()
    assert "<style>" in html
    assert "<!DOCTYPE html>" in html


def test_generate_html_empty_posts():
    output_dir = Path(tempfile.mkdtemp())
    path = generate_html([], output_dir)
    html = path.read_text()
    assert "0 new posts" in html


def test_generate_html_with_translation():
    posts = [
        {
            "author": "Test Author",
            "target_name": "Test Author",
            "target_type": "person",
            "text": "这是一段中文内容",
            "summary": "A summary in English about Chinese content.",
            "translation": "This is Chinese content.",
            "url": "https://linkedin.com/feed/update/urn:li:activity:004",
            "media_urls": [],
            "posted_at": "2026-02-14T10:00:00",
        },
    ]
    output_dir = Path(tempfile.mkdtemp())
    path = generate_html(posts, output_dir)
    html = path.read_text()
    assert "这是一段中文内容" in html
    assert "This is Chinese content." in html
    assert "Translation" in html
