@AGENTS.md

The authoritative workflow is [.agents/skills/msresearch-aurora-air-pollution/SKILL.md](.agents/skills/msresearch-aurora-air-pollution/SKILL.md). The project `.claude/skills` discovery adapter points at that same directory. Read [knowledge/index.md](knowledge/index.md) progressively. Register the local stdio server using the Claude Code example in [docs/agent-workflow.md](docs/agent-workflow.md); `.mcp.json` is client-specific. Scientific execution follows the canonical MCP/approval route.

For Claude Code CLI and its VS Code extension, the installable branch-pinned plugin is preferred; see [docs/claude-code-plugin.md](docs/claude-code-plugin.md). When the plugin is active, do not also add the repository-level `aurora_air_pollution` MCP server. The plugin packages the canonical instructions and knowledge inside its root; it does not rely on this checkout's `CLAUDE.md` being loaded.
