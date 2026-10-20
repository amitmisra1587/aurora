# Onboarding and agent interoperability validation

Validated on **2026-10-20**, Linux x86_64. These are installation and interoperability checks, separate from the historical scientific studies and the [scientific implementation report](workflow-implementation-report.md). The release targets branch `agent_skills_to_finetune_aurora`; the historical GitHub-install row below records its initial pre-release state.

## Problems and changes

| Original onboarding problem | Change |
| --- | --- |
| README started with a clone, multiple variables, manual bootstrap and configuration | Recommended route is two terminal plugin commands followed by a setup prompt; advanced setup moved to runbooks |
| Launcher required dependencies/config before the setup skill could inspect MCP | Dependency-free supervisor immediately serves setup status, installs only light pins in the background, validates/configures, then bridges to the existing SDK backend |
| Plugin cache might lack Git/build metadata and should not hold environments/data | `--no-project` bootstrap and launcher-controlled `PYTHONPATH`; all mutable paths are external |
| Workstation-specific Python/config paths in every client example | All examples use the same launcher; one optional external `launcher.json` stores persistent path choices |
| Updates could keep cached code or collide with an environment's old pins | Plugin bumped to `0.2.0`; default environments include Python and light-lock identity; existing configurations are preserved |
| Root `.mcp.json` doubled as project and plugin registration | Registration moved to the plugin manifest only; manual client examples remain separate |
| Setup skill assumed MCP already worked | It handles setup status/retry first, and diagnoses missing Python directly from its packaged launcher/runbook |
| Desktop/GPT claims conflated OKF, skills and tools | Canonical instructions exposed as MCP resources; compatibility table states discovery, transport, setup and actual test scope independently |

No model code, scientific recipe, architecture, checkpoint contract or resource limit was changed. Upstream README attribution, citation, examples and license sections remain intact.

## Files changed

| Files | Purpose |
| --- | --- |
| `README.md`, `docs/claude-code-plugin.md`, `docs/agent-workflow.md` | First interaction, installation, capabilities, paths, recovery, client routes and approval |
| `docs/onboarding-validation.md`, `docs/workflow-implementation-report.md` | This evidence record and links from the earlier scientific report |
| `bin/aurora-mcp`, new `scripts/launch_workflow.py` | Immediate setup connection, external configuration, background bootstrap, SDK forwarding and human approval entry |
| `scripts/bootstrap_workflow.py` | Cache-compatible `--no-project` mode and resumable marker before environment creation |
| `.claude-plugin/plugin.json`, removed `.mcp.json` | Version 0.2.0 and one plugin-only MCP registration; marketplace `./` source remains unchanged |
| `aurora_workflow/mcp_server.py` | Resources serving the exact canonical instructions/routing/evidence files |
| `.agents/skills/msresearch-aurora-air-pollution/SKILL.md`, `skills/aurora-setup/SKILL.md`, `CLAUDE.md`, `knowledge/operations/agents.md` | Setup before inspection, recovery, canonical routing and accurate resource access |
| `docs/clients/{claude-mcp.example.json,codex-config.example.toml,vscode-mcp.example.json}` | Client-specific schemas pointing to the shared launcher |
| `tests/workflow/test_claude_plugin.py`, `test_knowledge.py`, new `test_onboarding.py`, `.github/workflows/agent-workflow.yml` | Packaging, installed links/resources, configuration, failures/retry, optional fresh-install regression and CI coverage |
| `tests/vscode/{package.json,extension.cjs,test.cjs,run.py,README.md}` | Opt-in real VS Code Extension Development Host test and isolated-profile runner |

## Reference review

[Prithvi WxC skills](https://github.com/midatm1234/prithvi-wxc-skills) supplied the usability reference: short marketplace install, immediate setup status, external state, prompts and file locations. Aurora keeps its existing shared backend and bounded approval mechanism rather than copying Prithvi's scientific procedures or adding an untested HTTP deployment.

Official references checked on the validation date:

- Claude Code [plugin manifest](https://code.claude.com/docs/en/plugins-reference), [marketplace sources](https://code.claude.com/docs/en/plugins/marketplace-reference), [branch selection and updates](https://code.claude.com/docs/en/plugins/host-marketplace), [VS Code integration](https://code.claude.com/docs/en/vs-code), and [installation](https://code.claude.com/docs/en/setup).
- VS Code [skills](https://code.visualstudio.com/docs/agent-customization/agent-skills), [MCP configuration](https://code.visualstudio.com/docs/agent-customization/mcp-servers) and the [upstream stdio schema implementation](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/mcp/common/mcpConfiguration.ts).
- OpenAI [Codex skills](https://developers.openai.com/codex/skills/), [Codex MCP](https://developers.openai.com/codex/mcp/) and [ChatGPT remote MCP quickstart](https://developers.openai.com/plugins/build/app-quickstart).
- [Local MCP host setup](https://modelcontextprotocol.io/docs/develop/connect-local-servers), [Agent Skills specification](https://agentskills.io/specification), and the [canonical OKF specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md). The existing bundle's pinned evidence references remain historical source records; this review does not rewrite them as new science.

## What actually ran

| Check | Observed result / scope |
| --- | --- |
| Claude Code native CLI | **2.1.304**, installed under an isolated temporary home, without changing the user's client configuration |
| Real GitHub marketplace installation | `marketplace add midatm1234/aurora#agent_skills_to_finetune_aurora` and `plugin install aurora-air-pollution@aurora` succeeded; marketplace list reported the exact branch and `./` source resolved into its plugin cache |
| Published versus local version | Live branch at test time was commit `824520f1d8c9197afdcac70c44d59cda1715b53d`, plugin **0.1.0**. Revised **0.2.0** was installed separately through a local marketplace; this is not a claim that unpublished edits were downloaded from GitHub |
| Manifest validation | Actual `claude plugin validate` passed. It warned that root `CLAUDE.md` is not loaded as plugin context; retained for checkout users, while packaged skills explicitly link canonical instructions |
| Real plugin discovery | `claude plugin details aurora-air-pollution@aurora` reported all **five skills** and **one MCP server** for 0.2.0; inventory discovery is distinct from an authenticated skill invocation |
| Versioned update/cache behavior | Isolated local Git fixture, fetched by Claude's Git marketplace route: installed **0.1.0**, committed **0.2.0**, updated marketplace/plugin, then verified the new 0.2.0 cache and component inventory. Git URL rewriting kept this test local; no public release was created |
| Installed package, clean first run | Official SDK client spawned the actual installed launcher from an unrelated temporary working directory with a fresh home/config/cache and no data, credentials, weights or GPU assumption. It initialized within the test's five-second bound, installed light dependencies, discovered **26 tools** (24 workflow + 2 setup), and completed read-only inspection/knowledge calls |
| Resource and skill resolution | Canonical workflow/evidence files and OKF are packaged; regular-file plugin skills and the checkout Claude symlink are checked. SDK read all three `aurora://...` resource entries; `knowledge_validate` and root knowledge read succeeded |
| Restart/repeated setup | Reconnected to the same external environment/config, ran `--check`, and verified config bytes were unchanged |
| Recovery | Missing Python produced an actionable stderr error; malformed launcher JSON remained connected to setup tools and recovered via `setup_retry`; invalid workflow config was preserved; a real pip failure with `PIP_NO_INDEX=1` remained inspectable and retried its managed install state |
| Codex CLI | **0.162.0-alpha.17.2**; actual `mcp add`, `get --json`, per-invocation `list --json`, and removal succeeded in an isolated home; parsed launcher as enabled stdio. No authenticated Codex agent run |
| VS Code / installed extensions | VS Code **1.142.0** (commit `6d62b1d5dace93a33b3a6d3eca1317bd5e15bcb1`), Claude extension **2.1.304**, OpenAI extension **26.1007.21434** detected. A matching desktop build was launched under Xvfb with an isolated Extension Development Host; no user application settings were changed |
| Actual VS Code skill and MCP discovery | **PASSED**: `vscode.chat.getSkills` found the canonical `.agents/skills/.../SKILL.md`; the editor discovered exactly one workspace server from the unchanged supplied VS Code configuration, including `${workspaceFolder}` resolution |
| Actual VS Code tool calls | **PASSED**: first-run minimal installation, live tool-list refresh and all **26 tools**; `vscode.lm.invokeTool` successfully called `setup_status`, `inspect_environment`, `inspect_assets`, `list_runs` and `knowledge_validate`. Fork import verified; empty runs/assets handled; no NumPy, PyTorch or credentials |
| Actual Claude Code VS Code extension | **PASSED**: extension activation, documented editor-command registration, and its own bundled CLI reported Aurora 0.2.0 with all **five skills** and **one MCP server**. No authenticated/model chat was invoked |
| Client configuration | JSON/TOML parsing and distinct schema assertions: Codex `mcp_servers`, Claude/Desktop `mcpServers`, VS Code `servers`, supported launcher/args and workspace substitution. These are static/schema checks, not UI validation |
| SDK/runtime | MCP Python SDK **1.30.0**, protocol **2025-11-25**; Python **3.12.3** for tests/fresh environment. Shell host also has Python **3.13.13**; no 3.14/macOS/Windows execution claim |
| CPU scientific regression | Existing full suite: **118 passed, 2 skipped** (opt-in fresh network test and real CAMS/GPU). One NumPy/NetCDF binary-size runtime warning occurred; the associated tests passed |
| Explicit fresh-install regression | `AURORA_TEST_FRESH_INSTALL=1` onboarding module: **2 passed**, including actual minimal dependency installation from the installed package and deterministic pip-failure recovery |
| Final consistency checks | `git diff --check`, shell syntax and Python compilation passed; updated documentation links resolved; upstream README material compared byte-for-byte; final installed launcher/bootstrap/manifest/backend matched the working tree |

The lightweight environment contained neither NumPy nor PyTorch; credential-presence flags were false. No CAMS retrieval, pretrained download, real Aurora forecast, GPU training or scientific reproduction was performed for onboarding. Existing CPU tests use synthetic data and exercise workflow functionality only.

The real VS Code test finished with exit code **0** and `passed: true`. It uses test-only proposed discovery APIs plus the stable native tool-invocation API; those test flags are not required for ordinary use. Its initial harness run completed native skill/MCP/tool checks but asserted an unavailable optional Claude installation command. The final harness instead checks the documented editor command and the extension's bundled plugin inventory; the workflow implementation required no change. Full CPU regression was rerun: **118 passed, 2 expected skips**, with the same recorded numerical-library warning.

## Reproduce the automated checks

**Terminal**, in a checkout with the documented test dependencies:

```bash
python -m pytest --confcutdir=tests/workflow tests/workflow
```

To explicitly allow minimal package downloads into pytest's temporary home:

```bash
AURORA_TEST_FRESH_INSTALL=1 python -m pytest \
  --confcutdir=tests/workflow tests/workflow/test_onboarding.py
```

To test an actual installed snapshot, set `AURORA_TEST_LAUNCHER` to its absolute `bin/aurora-mcp` path on that last command. This is a maintainer check; normal users never need to locate the plugin cache. Tests remove developer Aurora/Python/XDG overrides and credential variables and set a temporary home. The default suite does not download scientific assets; its pip-failure check disables package indexes.

For the actual application test, follow [tests/vscode/README.md](../tests/vscode/README.md). It requires a desktop executable, installed Claude extension and display/Xvfb; it creates a separate home/profile and uses no model account. The final execution report and application logs were retained outside the repository under `/tmp/aurora-vscode-complete/`.

## Exact remaining client checks

1. **Authenticated Claude Code:** run the two README marketplace commands. Confirm `0.2.0` or later with `claude plugin list --json`; verify the marketplace ref and `plugin details` inventory, then `/aurora-air-pollution:aurora-setup`, `/mcp`, setup status and inspection. An attempted unauthenticated print session here returned “Not logged in”; model-driven behavior remains unverified.
2. **Claude Code VS Code chat:** extension activation and plugin inventory passed. Start/reload an authenticated session, invoke the namespaced setup skill and inspect through that session; this remaining check exercises the chat agent rather than the already-passing native tool API.
3. **Copilot in VS Code chat:** the actual application skill/configuration discovery and native MCP calls passed. With Copilot installed and authenticated, invoke the same tools from its chat agent. Copilot CLI/cloud are separate and unvalidated.
4. **Codex CLI/IDE:** open the checkout, register the launcher, restart, confirm `/mcp` and the canonical skill, then call the read-only tools. Registration parsing above does not establish an IDE/model session.
5. **Claude Desktop:** merge the stdio config with an absolute launcher path, restart, read `aurora://instructions` (or supply the canonical text), and call inspection tools. No Desktop application test was run.
6. **Mac / WSL2 / containers:** repeat the first-run tests on those platforms before claiming support. A Mac can target a Linux execution host using Remote SSH; no local CUDA path is provided. No Docker build or runtime validation was performed here.
7. **ChatGPT browser:** provide a separately deployed/authenticated remote MCP interface and execution environment before testing. This stdio-only branch supplies neither a hosted endpoint nor an automatic ChatGPT connector.
8. **Real science:** supply the correct CAMS permissions/data, pinned model/static assets, compatible refinement checkpoints and CUDA resources; inspect and approve a bounded scientific plan. Onboarding tests do not replace this evaluation.
