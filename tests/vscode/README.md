# Real VS Code integration smoke test

This opt-in test runs in an actual VS Code Extension Development Host. It checks
workspace skill discovery, the documented `.vscode/mcp.json` configuration,
automatic minimal setup, tool-list refresh, read-only MCP calls through
`vscode.lm.invokeTool`, Claude Code extension activation and its bundled plugin
inventory. It uses no chat model, credentials, datasets or scientific execution.

Requirements: Git, Python 3.12–3.14, a VS Code **desktop executable**, the installed
Claude Code extension and a display. On a Linux headless host, use an existing
Xvfb display. The VS Code Remote CLI alone is not a desktop executable.

From the repository root:

```bash
python tests/vscode/run.py \
  --code /absolute/path/to/VSCode-linux-x64/code \
  --claude-extension /absolute/path/to/anthropic.claude-code-extension \
  --display :91
```

The runner creates a disposable checkout, home, plugin installation, VS Code
profile and MCP configuration. It strips developer credential/environment
overrides; first setup installs only the light Python requirements. It prints
the result and the locations of its JSON report and VS Code log. No generated
files are written to the source checkout or normal client settings.

The test-only extension enables `chatPromptFiles` and `mcpServerDefinitions`
proposed APIs to inspect actual discovery. Ordinary users do not need these
flags or this test extension. The runner trusts only the reviewed server in its
disposable profile; it never grants scientific plan approval.

Validated with VS Code **1.142.0**, Claude Code extension **2.1.304**, Python
**3.12.3** on Linux x86_64. This establishes the VS Code configuration/tool path
and extension inventory. It does not establish an authenticated Claude,
Copilot or Codex chat session, real forecast skill, or macOS/Windows support.
