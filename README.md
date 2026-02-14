# ai4news

LinkedIn content aggregation and weekly newsletter generator, powered by Claude Code.

ai4news monitors LinkedIn company and person pages, extracts their latest posts via a real browser, stores them in a local database, and generates a self-contained HTML newsletter with AI-written summaries.

## How it works

ai4news is a **Claude Code skill + MCP server**. You don't run it directly -- you ask Claude to do it:

```
You: "Collect LinkedIn posts and generate a newsletter"
Claude: (invokes the ai4news skill, drives Chrome, extracts posts, writes summaries, outputs HTML)
```

Claude orchestrates everything: navigating LinkedIn in your browser via Chrome DevTools MCP, extracting posts with JavaScript, storing them through the ai4news MCP server, summarizing with AI, and rendering the final newsletter.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- [uv](https://docs.astral.sh/uv/) package manager
- Chrome browser with [Chrome DevTools MCP](https://github.com/anthropics/claude-code/tree/main/packages/mcp-server-chrome-devtools) connected
- Logged into LinkedIn in Chrome

## Setup

```bash
make install
```

This does three things:
1. Installs Python dependencies via `uv sync`
2. Registers the `ai4news` MCP server with Claude Code
3. Symlinks the skill into `~/.claude/skills/`

To uninstall:
```bash
make uninstall
```

## Usage

### 1. Configure targets

Edit `config/targets.yaml` to add LinkedIn pages to monitor:

```yaml
targets:
- name: Anthropic
  type: company
  url: https://www.linkedin.com/company/anthropicresearch
- name: OpenAI
  type: company
  url: https://www.linkedin.com/company/openai
- name: name_test
  type: person
  url: https://www.linkedin.com/in/name_test/
```

Supported types: `company`, `person`, `hashtag`.

You can also add/remove targets via Claude:
```
You: "Add Anthropic as a target: https://www.linkedin.com/company/anthropicresearch"
You: "Remove the OpenAI target"
```

### 2. Run the newsletter workflow

Open Claude Code and say:

```
You: "Collect LinkedIn posts and generate a newsletter"
```

Claude will:
1. Visit each target's LinkedIn page in your Chrome browser
2. Extract the latest 2-3 posts per target using JavaScript DOM queries
3. Store posts in the local SQLite database (with deduplication)
4. Summarize each post in English
5. Generate and open an HTML newsletter

### 3. View the output

The newsletter opens automatically in your browser. Files are saved to `data/newsletters/`.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Claude Code                         │
│                                                          │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │  SKILL.md    │────>│  Claude (orchestrator)        │  │
│  │  (workflow)  │     │  - navigates pages            │  │
│  └──────────────┘     │  - extracts posts via JS      │  │
│                       │  - writes AI summaries        │  │
│                       │  - calls MCP tools            │  │
│                       └──────┬───────────┬────────────┘  │
│                              │           │               │
│                    ┌─────────▼──┐  ┌─────▼──────────┐   │
│                    │ Chrome     │  │ ai4news        │   │
│                    │ DevTools   │  │ MCP Server     │   │
│                    │ MCP        │  │ (Python)       │   │
│                    └─────┬──────┘  └──┬─────────────┘   │
│                          │            │                  │
└──────────────────────────│────────────│──────────────────┘
                           │            │
                    ┌──────▼──────┐  ┌──▼──────────────┐
                    │  Chrome     │  │  SQLite DB      │
                    │  Browser    │  │  (data/)        │
                    │  (LinkedIn) │  ├─────────────────┤
                    └─────────────┘  │  targets        │
                                     │  posts          │
                                     │  newsletters    │
                                     └─────────────────┘
```

### Components

**Skill definition** (`skill/SKILL.md`) -- The workflow Claude follows. Defines the step-by-step process: get targets, scrape via Chrome DevTools, generate newsletter. Contains the JavaScript extraction function that pulls post data directly from LinkedIn's DOM.

**MCP Server** (`src/ai4news/server.py`) -- Exposes tools that Claude calls during the workflow:
- `list_targets` / `add_target` / `remove_target` -- manage monitored LinkedIn pages
- `store_posts` -- save extracted posts with deduplication on `linkedin_id`
- `get_new_posts` -- query posts from the last N days
- `generate_newsletter` -- render posts + summaries into HTML
- `open_newsletter` -- open the HTML file in the browser

**Storage** (`src/ai4news/storage.py`) -- SQLite database with three tables:
- `targets` -- LinkedIn pages to monitor (URL, type, name)
- `posts` -- extracted posts, deduplicated by `linkedin_id` (`urn:li:activity:...`)
- `newsletters` -- record of generated newsletters

**Config** (`src/ai4news/config.py`) -- Reads/writes `config/targets.yaml`.

**Newsletter renderer** (`src/ai4news/newsletter.py`) -- Jinja2 template that produces a self-contained HTML file. Posts are grouped by target, with summaries, translations (for non-English content), and links to originals.

### Post extraction

Posts are extracted using `evaluate_script` (Chrome DevTools MCP), which runs JavaScript directly in the LinkedIn page DOM. This approach:
- Returns ~1KB of structured JSON instead of 74KB+ a11y tree snapshots
- Provides stable `urn:li:activity:...` IDs from `data-urn` attributes for reliable deduplication
- Extracts individual post URLs (`/feed/update/urn:li:activity:...`)

The `take_snapshot` tool is only used once per target for login wall detection.

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/ -v
```

## Project structure

```
ai4news/
├── config/
│   └── targets.yaml          # LinkedIn targets to monitor
├── data/                      # Runtime data (gitignored)
│   ├── ai4news.db            # SQLite database
│   └── newsletters/          # Generated HTML files
├── skill/
│   └── SKILL.md              # Claude Code skill definition
├── src/ai4news/
│   ├── config.py             # YAML config reader
│   ├── storage.py            # SQLite database layer
│   ├── newsletter.py         # HTML newsletter renderer
│   └── server.py             # MCP server (tool definitions)
├── tests/                     # pytest test suite
├── Makefile                   # install/uninstall commands
└── pyproject.toml             # Python project config
```
