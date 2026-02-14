PROJECT_DIR := $(shell pwd)
SKILL_TARGET := $(HOME)/.claude/skills/ai4news

.PHONY: install uninstall login

install:
	uv sync
	uv run playwright install chromium
	claude mcp add ai4news -- uv run --directory $(PROJECT_DIR) ai4news-server
	mkdir -p $(HOME)/.claude/skills
	ln -sfn $(PROJECT_DIR)/skill $(SKILL_TARGET)
	@echo ""
	@echo "Installation complete."
	@echo "  MCP Server: registered as 'ai4news'"
	@echo "  Skill: linked at $(SKILL_TARGET)"
	@echo ""
	@echo "Next: run 'make login' to log in to LinkedIn."

uninstall:
	claude mcp remove ai4news || true
	rm -f $(SKILL_TARGET)
	@echo "Uninstalled ai4news MCP server and skill."

login:
	uv run python -c "import asyncio; from ai4news.scraper import open_login_browser; asyncio.run(open_login_browser())"
