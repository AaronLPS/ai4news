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
3. **Login wall check:** Use `take_snapshot` and check for login wall indicators (text like "Sign in", "Join now", or no post content). If detected, stop and inform the user:
   > "LinkedIn requires login. Please log into LinkedIn in your Chrome browser, then try again."
4. **Scroll once:** Use `evaluate_script` to scroll down once and load a few more posts:
   ```javascript
   async () => {
     window.scrollBy(0, 1500);
     await new Promise(r => setTimeout(r, 2000));
   }
   ```
5. **Extract posts via JS:** Use `evaluate_script` to extract the top 3 posts directly from the DOM. This avoids large snapshots and returns compact JSON with stable IDs:
   ```javascript
   () => {
     const posts = document.querySelectorAll(
       '[data-urn*="urn:li:activity"], .feed-shared-update-v2, .occludable-update'
     );
     return Array.from(posts).slice(0, 3).map(el => {
       const urn = el.getAttribute('data-urn') || '';
       const idMatch = urn.match(/urn:li:activity:\d+/);
       const authorEl = el.querySelector(
         '.update-components-actor__name span[aria-hidden="true"], ' +
         '.feed-shared-actor__name span[aria-hidden="true"]'
       );
       const textEl = el.querySelector(
         '.feed-shared-update-v2__description, ' +
         '.update-components-text, .feed-shared-text'
       );
       const linkEl = el.querySelector('a[href*="feed/update"]');
       const timeEl = el.querySelector('time');
       const imgs = el.querySelectorAll(
         '.feed-shared-image__image, .update-components-image img'
       );
       const linkedinId = idMatch ? idMatch[0] : null;
       return {
         linkedin_id: linkedinId,
         author: authorEl ? authorEl.innerText.trim() : 'Unknown',
         text: textEl ? textEl.innerText.trim().slice(0, 500) : '',
         url: linkEl ? linkEl.href : (linkedinId ? 'https://www.linkedin.com/feed/update/' + linkedinId : ''),
         media_urls: Array.from(imgs).map(i => i.src).filter(Boolean),
         posted_at: timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText.trim()) : '',
       };
     }).filter(p => p.linkedin_id);
   }
   ```
6. **Fallback:** If the JS extraction returns an empty array (e.g. LinkedIn changed selectors), fall back to `take_snapshot` of the **current visible area only** (no additional scrolling) and extract posts from the snapshot text. Use snapshot-extracted data as best-effort -- IDs may not be stable.
7. **Store posts:** Call `store_posts(target_url=<target's base url>, posts=<extracted posts list>)`

### Step 3: Generate newsletter

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
