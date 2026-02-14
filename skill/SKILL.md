---
name: linkedin-weekly
description: Use when collecting LinkedIn posts from followed targets and generating a weekly newsletter digest with AI summaries
---

# LinkedIn Weekly Newsletter

## Overview

Collect new LinkedIn posts from configured targets, summarize each, and generate a weekly HTML newsletter.

## Workflow

1. Call `scrape_targets` to fetch latest posts from all targets
2. Call `get_new_posts` with since_days=7
3. For each post returned, generate a one-sentence English summary
4. If original post text is non-English, also generate an English translation
5. Group posts by target_name, sort by posted_at (newest first)
6. Call `generate_newsletter` passing the list of posts, each with added `summary` field (and `translation` field if applicable)
7. Call `open_newsletter` with the returned file path
8. Report to user: total targets checked, new posts found, newsletter file path

## Summary Guidelines

- Always write summaries in English regardless of original language
- One sentence per post capturing the core point
- If post contains links or media, mention briefly
- Keep original post text in its original language
- For non-English posts, add a `translation` field with full English translation
