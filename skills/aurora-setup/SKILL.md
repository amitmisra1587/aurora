---
name: aurora-setup
description: Check a local machine, existing Aurora assets and runs, then prepare the lightweight or scientific environment. Use before CAMS acquisition, training, or inference on a new machine.
---

# Prepare a local Aurora workflow

The plugin runs locally. First read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md) and [runbook](../../docs/claude-code-plugin.md); they are inside this plugin checkout.

1. Call `inspect_environment`, `inspect_assets`, and `list_runs` before proposing setup. Summarize existing roots, dependencies, credentials-presence (never values), assets, checkpoints and reusable outputs.
2. Call `validate_recipe` for the selected versioned recipe. Do not download model files or load PyTorch to answer setup questions.
3. If the pinned local MCP environment is absent, show the runbook's explicit `bin/aurora-mcp --install` and configure/doctor commands. Do not run arbitrary setup shell commands or overwrite an existing environment. For data preparation without model dependencies use the `--data` profile; for CPU synthetic science use a separate `--science` environment.
4. Ask the operator to enter ADS credentials only in the local ADS config file and manually accept the dataset terms in their ADS account. Never ask for credentials in chat.
5. Call `inspect_environment`, `inspect_assets`, and `list_runs` again after the operator configures the machine. Report blockers and which workflow modes the machine can actually support.

This skill does not authorize downloads, asset retrieval, model loading, or training. For expensive stages, `aurora-reproduce` or `aurora-cams-data` creates a bounded plan; the operator approves it in their own terminal.
