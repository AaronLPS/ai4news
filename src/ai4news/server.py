# src/ai4news/server.py
import asyncio
import subprocess
import sys
import webbrowser
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ai4news.config import get_data_dir, load_targets, save_targets
from ai4news.storage import Database
from ai4news.scraper import scrape_all_targets, open_login_browser
from ai4news.newsletter import generate_html

mcp = FastMCP(
    name="ai4news",
    instructions="LinkedIn content aggregation tools for weekly newsletter generation.",
)


def _get_db() -> Database:
    return Database(get_data_dir() / "ai4news.db")


@mcp.tool()
async def scrape_targets() -> dict:
    """Scrape latest LinkedIn posts from all configured targets.
    Uses persistent Browser Profile for login session.
    Returns scraped count, new count, and any errors.
    """
    db = _get_db()
    try:
        result = await scrape_all_targets(db)
        return result
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
        tid = db.upsert_target(url=url, target_type=target_type, name=name)
        targets = load_targets()
        if not any(t["url"] == url for t in targets):
            targets.append({"type": target_type, "name": name, "url": url})
            save_targets(targets)
        return {"id": tid, "url": url, "type": target_type, "name": name}
    finally:
        db.close()


@mcp.tool()
def remove_target(url: str) -> dict:
    """Remove a LinkedIn target from monitoring."""
    db = _get_db()
    try:
        removed = db.remove_target(url)
        if removed:
            targets = load_targets()
            targets = [t for t in targets if t["url"] != url]
            save_targets(targets)
        return {"removed": removed, "url": url}
    finally:
        db.close()


@mcp.tool()
def list_targets() -> list[dict]:
    """List all configured LinkedIn targets."""
    db = _get_db()
    try:
        return db.list_targets()
    finally:
        db.close()


@mcp.tool()
async def login() -> str:
    """Open a browser window for manual LinkedIn login.
    Session is saved to persistent Browser Profile for future scraping.
    """
    return await open_login_browser()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
