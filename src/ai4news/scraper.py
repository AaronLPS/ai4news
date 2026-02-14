# src/ai4news/scraper.py
import asyncio
import logging
import random
import re

from playwright.async_api import async_playwright, Page

from ai4news.config import get_data_dir, load_targets
from ai4news.storage import Database

logger = logging.getLogger(__name__)

SCROLL_COUNT = 5
SCROLL_DELAY_MIN = 2.0
SCROLL_DELAY_MAX = 4.0
PAGE_LOAD_DELAY_MIN = 1.0
PAGE_LOAD_DELAY_MAX = 3.0


def build_activity_url(base_url: str, target_type: str) -> str:
    url = base_url.rstrip("/")
    if target_type == "person":
        return f"{url}/recent-activity/all/"
    elif target_type == "company":
        return f"{url}/posts/"
    else:
        return url


def extract_linkedin_id_from_url(url: str) -> str | None:
    match = re.search(r"(urn:li:activity:\d+)", url)
    return match.group(1) if match else None


async def _scroll_page(page: Page) -> None:
    for _ in range(SCROLL_COUNT):
        await page.evaluate("window.scrollBy(0, 1000)")
        await asyncio.sleep(random.uniform(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX))


async def _extract_posts_from_page(page: Page) -> list[dict]:
    posts = []
    selectors = [
        "[data-urn*='urn:li:activity']",
        ".feed-shared-update-v2",
        ".occludable-update",
    ]

    elements = []
    for selector in selectors:
        elements = await page.query_selector_all(selector)
        if elements:
            break

    for el in elements:
        try:
            data_urn = await el.get_attribute("data-urn")
            post_url_el = await el.query_selector("a[href*='feed/update']")
            post_url = ""
            if post_url_el:
                post_url = await post_url_el.get_attribute("href") or ""

            linkedin_id = None
            if data_urn:
                linkedin_id = extract_linkedin_id_from_url(data_urn)
            if not linkedin_id and post_url:
                linkedin_id = extract_linkedin_id_from_url(post_url)
            if not linkedin_id:
                continue

            author_el = await el.query_selector(
                ".update-components-actor__name span[aria-hidden='true'],"
                ".feed-shared-actor__name span[aria-hidden='true']"
            )
            author = (await author_el.inner_text()).strip() if author_el else "Unknown"

            text_el = await el.query_selector(
                ".feed-shared-update-v2__description,"
                ".update-components-text,"
                ".feed-shared-text"
            )
            text = (await text_el.inner_text()).strip() if text_el else ""

            media_urls = []
            img_els = await el.query_selector_all(
                ".feed-shared-image__image, .update-components-image img"
            )
            for img in img_els:
                src = await img.get_attribute("src")
                if src:
                    media_urls.append(src)

            time_el = await el.query_selector("time")
            posted_at = ""
            if time_el:
                posted_at = await time_el.get_attribute("datetime") or ""

            if not post_url and linkedin_id:
                post_url = f"https://www.linkedin.com/feed/update/{linkedin_id}"

            posts.append({
                "linkedin_id": linkedin_id,
                "author": author,
                "text": text,
                "url": post_url,
                "media_urls": media_urls,
                "posted_at": posted_at,
            })
        except Exception as e:
            logger.warning(f"Failed to extract post: {e}")
            continue

    return posts


async def scrape_all_targets(db: Database) -> dict:
    data_dir = get_data_dir()
    profile_dir = data_dir / "browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    targets = load_targets()
    total_scraped = 0
    total_new = 0
    errors = []

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=True,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        page = await context.new_page()

        for target in targets:
            try:
                target_id = db.upsert_target(
                    url=target["url"],
                    target_type=target["type"],
                    name=target.get("name", ""),
                )
                activity_url = build_activity_url(target["url"], target["type"])

                await page.goto(activity_url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(PAGE_LOAD_DELAY_MIN, PAGE_LOAD_DELAY_MAX))
                await _scroll_page(page)

                posts = await _extract_posts_from_page(page)
                target_new = 0
                for post_data in posts:
                    inserted = db.insert_post(
                        target_id=target_id,
                        linkedin_id=post_data["linkedin_id"],
                        author=post_data["author"],
                        text=post_data["text"],
                        url=post_data["url"],
                        media_urls=post_data["media_urls"],
                        posted_at=post_data["posted_at"],
                    )
                    if inserted:
                        target_new += 1

                total_scraped += len(posts)
                total_new += target_new
                logger.info(
                    f"Scraped {target.get('name', target['url'])}: "
                    f"{len(posts)} posts, {target_new} new"
                )

            except Exception as e:
                error_msg = f"Error scraping {target.get('name', target['url'])}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        await context.close()

    return {"scraped": total_scraped, "new": total_new, "errors": errors}


async def open_login_browser() -> str:
    data_dir = get_data_dir()
    profile_dir = data_dir / "browser_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        print("Please log in to LinkedIn in the browser window.")
        print("Press Enter here when done...")
        await asyncio.get_running_loop().run_in_executor(None, input)
        await context.close()

    return "Login session saved to browser profile."
