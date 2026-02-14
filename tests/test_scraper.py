# tests/test_scraper.py
from ai4news.scraper import (
    build_activity_url,
    extract_linkedin_id_from_url,
)


def test_build_activity_url_person():
    url = build_activity_url(
        "https://www.linkedin.com/in/satyanadella", "person"
    )
    assert url == "https://www.linkedin.com/in/satyanadella/recent-activity/all/"


def test_build_activity_url_company():
    url = build_activity_url(
        "https://www.linkedin.com/company/openai", "company"
    )
    assert url == "https://www.linkedin.com/company/openai/posts/"


def test_build_activity_url_hashtag():
    url = build_activity_url(
        "https://www.linkedin.com/feed/hashtag/ai", "hashtag"
    )
    assert url == "https://www.linkedin.com/feed/hashtag/ai"


def test_build_activity_url_strips_trailing_slash():
    url = build_activity_url(
        "https://www.linkedin.com/in/satyanadella/", "person"
    )
    assert url == "https://www.linkedin.com/in/satyanadella/recent-activity/all/"


def test_extract_linkedin_id_from_url():
    lid = extract_linkedin_id_from_url(
        "https://www.linkedin.com/feed/update/urn:li:activity:7296543210"
    )
    assert lid == "urn:li:activity:7296543210"


def test_extract_linkedin_id_from_url_with_query():
    lid = extract_linkedin_id_from_url(
        "https://www.linkedin.com/feed/update/urn:li:activity:123?utm=test"
    )
    assert lid == "urn:li:activity:123"


def test_extract_linkedin_id_from_url_no_match():
    lid = extract_linkedin_id_from_url("https://www.linkedin.com/in/someone")
    assert lid is None
