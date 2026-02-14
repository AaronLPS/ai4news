# src/ai4news/server.py
import webbrowser
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ai4news.config import get_data_dir, load_targets, save_targets
from ai4news.storage import Database
from ai4news.newsletter import generate_html

mcp = FastMCP(
    name="ai4news",
    instructions="LinkedIn content aggregation tools for weekly newsletter generation.",
)


def _get_db() -> Database:
    return Database(get_data_dir() / "ai4news.db")


def _build_activity_url(base_url: str, target_type: str) -> str:
    """Build the LinkedIn activity/posts URL for a target."""
    url = base_url.rstrip("/")
    if target_type == "person":
        return f"{url}/recent-activity/all/"
    elif target_type == "company":
        return f"{url}/posts/"
    else:
        return url


@mcp.tool()
def store_posts(target_url: str, posts: list[dict]) -> dict:
    """Store posts extracted by the AI from a LinkedIn target page.

    target_url: the base LinkedIn URL of the target (must match a configured target).
    posts: list of post dicts, each with keys:
        - linkedin_id (required): unique post ID, e.g. "urn:li:activity:123"
        - author: post author name
        - text: post body text
        - url: direct link to the post
        - media_urls: list of image/video URLs
        - posted_at: ISO timestamp or relative string
    Returns dict with stored count, new count, and any errors.
    """
    db = _get_db()
    try:
        normalized_url = target_url.rstrip("/")
        targets = db.list_targets()
        target = None
        for t in targets:
            if t["url"].rstrip("/") == normalized_url:
                target = t
                break
        if target is None:
            return {"error": f"Unknown target URL: {target_url}. Use list_targets to see configured targets."}

        target_id = target["id"]
        stored = 0
        new = 0
        errors = []
        for post in posts:
            linkedin_id = post.get("linkedin_id")
            if not linkedin_id:
                errors.append("Skipped post with missing linkedin_id")
                continue
            inserted = db.insert_post(
                target_id=target_id,
                linkedin_id=linkedin_id,
                author=post.get("author", "Unknown"),
                text=post.get("text", ""),
                url=post.get("url", ""),
                media_urls=post.get("media_urls", []),
                posted_at=post.get("posted_at", ""),
            )
            stored += 1
            if inserted:
                new += 1
        return {"stored": stored, "new": new, "duplicates": stored - new, "errors": errors}
    finally:
        db.close()


@mcp.tool()
def get_new_posts(since_days: int = 7) -> list[dict]:
    """Get posts scraped within the specified number of days.
    Returns list of posts with author, text, url, media_urls, timestamps.
    """
    db = _get_db()
    try:
        return db.get_new_posts(since_days=since_days)
    finally:
        db.close()


@mcp.tool()
def generate_newsletter(posts_with_summaries: list[dict]) -> str:
    """Receive posts with AI-generated summaries, render to HTML newsletter file.
    Each post dict should have: author, target_name, text, summary, url, media_urls, posted_at.
    Optional: translation (for non-English posts).
    Returns path to generated HTML file.
    """
    db = _get_db()
    output_dir = get_data_dir() / "newsletters"
    try:
        path = generate_html(posts_with_summaries, output_dir)
        db.record_newsletter(file_path=str(path), post_count=len(posts_with_summaries))
        return str(path)
    finally:
        db.close()


@mcp.tool()
def open_newsletter(file_path: str) -> str:
    """Open a newsletter HTML file in the default browser."""
    path = Path(file_path)
    if not path.exists():
        return f"Error: file not found: {file_path}"
    webbrowser.open(f"file://{path.resolve()}")
    return f"Opened {file_path} in browser."


@mcp.tool()
def add_target(url: str, target_type: str, name: str = "") -> dict:
    """Add a LinkedIn target to follow.
    target_type must be: person, company, or hashtag.
    """
    if target_type not in ("person", "company", "hashtag"):
        return {"error": f"Invalid type: {target_type}. Must be person, company, or hashtag."}
    db = _get_db()
    try:
        targets = load_targets()
        needs_yaml_update = not any(t["url"] == url for t in targets)
        if needs_yaml_update:
            targets.append({"type": target_type, "name": name, "url": url})
            save_targets(targets)
        tid = db.upsert_target(url=url, target_type=target_type, name=name)
        return {"id": tid, "url": url, "type": target_type, "name": name}
    except Exception:
        if needs_yaml_update:
            targets = [t for t in targets if t["url"] != url]
            save_targets(targets)
        raise
    finally:
        db.close()


@mcp.tool()
def remove_target(url: str) -> dict:
    """Remove a LinkedIn target from monitoring."""
    db = _get_db()
    try:
        targets_before = load_targets()
        removed = db.remove_target(url)
        if removed:
            updated = [t for t in targets_before if t["url"] != url]
            save_targets(updated)
        return {"removed": removed, "url": url}
    finally:
        db.close()


@mcp.tool()
def list_targets() -> list[dict]:
    """List all configured LinkedIn targets with their activity URLs.
    Each target includes: id, url, type, name, created_at, activity_url.
    Use activity_url with Chrome DevTools navigate_page to visit the target's posts.
    """
    db = _get_db()
    try:
        targets = db.list_targets()
        for t in targets:
            t["activity_url"] = _build_activity_url(t["url"], t["type"])
        return targets
    finally:
        db.close()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
