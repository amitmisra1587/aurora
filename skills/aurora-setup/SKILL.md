---
name: aurora-setup
description: Check a local machine, existing Aurora assets and runs, then prepare the lightweight or scientific environment. Use before CAMS acquisition, training, or inference on a new machine.
---

# Prepare a local Aurora workflow

The plugin runs locally. First read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md) and [runbook](../../docs/claude-code-plugin.md); they are inside this plugin checkout.

1. On first connection, call `setup_status` if inspection tools are not available. The launcher prepares the minimal MCP environment and default configuration in the background. Explain progress; after a failed install or invalid config, follow its recovery instructions and call `setup_retry`. If MCP itself cannot start, read the runbook and run the packaged `../../bin/aurora-mcp --check` resolved from this skill's directory; diagnose Python/PATH first. Do not require MCP tools to repair missing MCP prerequisites. No clone or plugin-cache lookup is needed.
2. Once ready, call `inspect_environment`, `inspect_assets`, and `list_runs`. Summarize existing roots, dependencies, credentials-presence (never values), assets, checkpoints and reusable outputs. Check `~/.config/aurora/launcher.json` (or XDG config location) for workspace/environment overrides; preserve existing configuration and compatible environments.
3. Call `validate_recipe` for the selected versioned recipe. Do not download model files or load PyTorch to answer setup questions.
4. Install larger dependencies only for a requested capability, using the runbook's `--data` or `--science` bootstrap in a distinct external environment, or reuse an already compatible scientific environment. Select it with launcher.json and reconnect. Never overwrite an unrelated environment or install CUDA packages for lightweight inspection.
5. For requested CAMS acquisition, ask the operator to enter ADS credentials only in the local ADS config file and manually accept the dataset terms in their ADS account. Never ask for credentials in chat.
6. Call inspection tools again after setup. Report actual CPU/GPU capabilities, blockers, configuration/output paths and the distinction between setup success and scientific reproduction.

This skill does not authorize downloads, asset retrieval, model loading, or training. For expensive stages, `aurora-reproduce` or `aurora-cams-data` creates a bounded plan; the operator approves it in their own terminal.
