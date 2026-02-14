---
name: linkedin-weekly
description: Use when collecting LinkedIn posts from followed targets and generating a weekly newsletter digest with AI summaries
---

# LinkedIn Weekly Newsletter

## Overview

Collect new LinkedIn posts from configured targets using Chrome DevTools MCP (real browser), summarize each, and generate a weekly HTML newsletter.

## Prerequisites

- User must be logged into LinkedIn in their Chrome browser
- Chrome DevTools MCP must be connected

## Workflow

### Step 1: Get targets

Call `list_targets` to get all configured targets. Each target includes an `activity_url` field -- this is the URL to visit for that target's posts.

### Step 2: Scrape each target via Chrome DevTools

For each target:

1. **Navigate:** Use `navigate_page` (Chrome DevTools MCP) to open the target's `activity_url`
2. **Wait for content:** Use `wait_for` to wait for post content to appear (e.g. text "activity" or a known page element)
3. **Scroll for more posts:** Use `evaluate_script` to scroll down and load more posts:
   ```javascript
   async () => {
     for (let i = 0; i < 5; i++) {
       window.scrollBy(0, 1000);
       await new Promise(r => setTimeout(r, 2000));
     }
   }
   ```
4. **Take snapshot:** Use `take_snapshot` to get a text representation of the page
5. **Extract posts:** From the snapshot text, extract each post with these fields:
   - `linkedin_id`: look for URN patterns like `urn:li:activity:DIGITS` in links or data attributes. If no URN found, generate a deterministic ID from the post content (e.g. hash of author+first 100 chars of text)
   - `author`: the name of the person/company who posted
   - `text`: the full post body text
   - `url`: direct link to the post (often contains the URN)
   - `media_urls`: list of any image or video URLs
   - `posted_at`: timestamp or relative time string (e.g. "2d ago", "1w")
6. **Store posts:** Call `store_posts(target_url=<target's base url>, posts=<extracted posts list>)`

### Step 3: Detect login walls

If a snapshot shows a login page (text like "Sign in", "Join now", or no post content), stop and inform the user:
> "LinkedIn requires login. Please log into LinkedIn in your Chrome browser, then try again."

### Step 4: Generate newsletter

1. Call `get_new_posts(since_days=7)` to retrieve all posts from the past week
2. For each post, generate a one-sentence English summary
3. If original post text is non-English, also generate an English translation
4. Group posts by `target_name`, sort by `posted_at` (newest first)
5. Call `generate_newsletter` passing the list of posts, each with added `summary` field (and `translation` field if applicable)
6. Call `open_newsletter` with the returned file path
7. Report to user: total targets checked, new posts found, newsletter file path

## Summary Guidelines

- Always write summaries in English regardless of original language
- One sentence per post capturing the core point
- If post contains links or media, mention briefly
- Keep original post text in its original language
- For non-English posts, add a `translation` field with full English translation
