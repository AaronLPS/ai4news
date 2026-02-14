PROJECT_DIR := $(shell pwd)
SKILL_TARGET := $(HOME)/.claude/skills/ai4news

.PHONY: install uninstall

install:
	uv sync
	claude mcp add ai4news -- uv run --directory $(PROJECT_DIR) ai4news-server
	mkdir -p $(HOME)/.claude/skills
	ln -sfn $(PROJECT_DIR)/skill $(SKILL_TARGET)
	@echo ""
	@echo "Installation complete."
	@echo "  MCP Server: registered as 'ai4news'"
	@echo "  Skill: linked at $(SKILL_TARGET)"
	@echo ""
	@echo "Ensure you are logged into LinkedIn in Chrome before using."

uninstall:
	claude mcp remove ai4news || true
	rm -f $(SKILL_TARGET)
	@echo "Uninstalled ai4news MCP server and skill."
