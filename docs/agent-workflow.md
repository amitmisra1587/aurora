# Use the Aurora workflow with your agent

The branch supplies code, skills, recipes and [OKF knowledge](../knowledge/index.md). You supply compute, ADS access and any unpublished trained checkpoint. [AGENTS.md](../AGENTS.md) routes all clients to one [canonical scientific skill](../.agents/skills/msresearch-aurora-air-pollution/SKILL.md). Thin client adapters carry discovery and routing, without duplicating model procedures.

## Start here

Claude Code CLI and VS Code users should follow the [two-command README install](../README.md#install-in-claude-code); no clone or manual environment is required. The [Claude runbook](claude-code-plugin.md) explains default paths, first-run status, scientific dependency profiles, Docker and recovery.

For other local clients, **run in a terminal**:

```bash
git clone --branch agent_skills_to_finetune_aurora --single-branch \
  https://github.com/midatm1234/aurora.git
cd aurora
bin/aurora-mcp --check
```

Requirements: Git, Python 3.12–3.14 with venv/pip, network access and writable external storage. The launcher prepares only the pinned metadata/MCP environment and creates a missing external config. It works from any working directory and uses the packaged fork rather than a PyPI/weather substitute. Default locations and optional persistent `launcher.json` overrides are in the [runbook](claude-code-plugin.md#paths-and-environments).

First call `setup_status`, then `inspect_environment`, `inspect_assets`, `list_runs` and `knowledge_validate`. An empty machine is valid: missing data/checkpoints and science packages are reported prerequisites. Setup success means connected tools and inspected roots, not scientific execution. Select/install larger environments only for requested data, CPU analysis/fixtures or CUDA science; preserve compatible artifacts and existing configuration.

## Client setup

These routes run the same **local stdio** launcher. MCP is not skill installation, and OKF readability is not proof of either. The [validation record](onboarding-validation.md) distinguishes static checks, actual SDK traffic and client applications.

### Claude Code CLI and VS Code extension

Use the marketplace plugin. Namespaced skills live in packaged `skills/`, referring to canonical `.agents/skills/` instructions and `knowledge/` inside the same plugin. The `mcpServers` field in `.claude-plugin/plugin.json` registers `${CLAUDE_PLUGIN_ROOT}/bin/aurora-mcp` automatically. The extension shares CLI installations; restart its session after changes. Check `/plugin`, `/aurora-air-pollution:aurora-setup`, `/mcp`, then make inspection calls.

Without the plugin, a checkout exposes the canonical skill through `.claude/skills/msresearch-aurora-air-pollution`, a symlink to `.agents/skills/...`. Relative reference links must be resolved against the **real canonical directory**. If a checkout loses symlinks or a host resolves links against the adapter path, read `CLAUDE.md` / `AGENTS.md` and the canonical file directly; do not claim automatic discovery in that environment. The plugin's five regular-file skills avoid symlink dependency.

For this manual route only, **terminal**, from any directory:

```bash
claude mcp add --transport stdio --scope local aurora_air_pollution -- /absolute/path/aurora/bin/aurora-mcp
claude mcp get aurora_air_pollution
```

Do not add it while the plugin's server is enabled. The bundled registration lives only in the plugin manifest; there is deliberately no root `.mcp.json` that could also start a project-scope copy. [Official MCP guide](https://code.claude.com/docs/en/mcp), [plugin reference](https://code.claude.com/docs/en/plugins-reference).

### OpenAI Codex CLI and IDE extension

Open/work in the branch checkout. Codex discovers the canonical `.agents/skills/msresearch-aurora-air-pollution/SKILL.md`; `AGENTS.md` provides project routing. **Terminal:**

```bash
codex mcp add aurora_air_pollution -- /absolute/path/aurora/bin/aurora-mcp
codex mcp list
```

Alternatively merge [codex-config.example.toml](clients/codex-config.example.toml) into **`~/.codex/config.toml`**, substituting your launcher path. It uses `mcp_servers` TOML. The immediate setup connection avoids a long startup timeout. Restart the Codex session, check `/mcp`, invoke `$msresearch-aurora-air-pollution`, and call inspection tools. CLI and IDE share MCP configuration; this does not configure a hosted cloud worker. [Official skills](https://developers.openai.com/codex/skills/) and [MCP](https://developers.openai.com/codex/mcp/) documentation.

### GitHub Copilot in VS Code agent mode

Open the branch checkout and use agent mode. VS Code supports `.agents/skills/` as a repository skill location, so no extra symlink or second copy is required. `.github/copilot-instructions.md` links the same canonical source. Check the agent's customizations/skills view for `msresearch-aurora-air-pollution`; skill availability does not guarantee invocation on every prompt.

Copy [vscode-mcp.example.json](clients/vscode-mcp.example.json) into your local **`.vscode/mcp.json`**. This is a VS Code `servers` object with `type: stdio` and `${workspaceFolder}/bin/aurora-mcp`, not Claude's `mcpServers` JSON. With a multi-root workspace, bind it to the Aurora root or replace the variable with an absolute launcher path. Use **MCP: List Servers** to start/trust the entry, inspect its tools and call `setup_status` and `inspect_environment`. Keep local paths/secrets out of commits. [Official skills](https://code.visualstudio.com/docs/agent-customization/agent-skills) and [MCP schema/setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

This setup is specifically Copilot **in VS Code**. Copilot CLI uses its own MCP configuration; GitHub's cloud coding agent runs in a separate provisioned environment with its own network, credentials and compute. Neither inherits `.vscode/mcp.json` or your local GPU. Those surfaces are not validated here.

The [real VS Code smoke test](../tests/vscode/README.md) passed in VS Code 1.142.0: the application discovered the canonical skill and this workspace server, refreshed from setup tools to all 26 tools, and invoked inspection and knowledge tools through its native tool API. Claude Code extension activation and bundled plugin inventory also passed. Authenticated Copilot/Claude/Codex chat sessions remain separate, untested checks.

### Claude Desktop and other local MCP hosts

Clone the branch, then merge [claude-mcp.example.json](clients/claude-mcp.example.json) into the host's **local stdio configuration** with your absolute launcher path. For Claude Desktop this is the `mcpServers` section of `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows Desktop alone does not make this Linux/macOS launcher a native Windows worker). Restart the application and inspect tools. [Official local MCP host guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

Desktop does not install Claude Code marketplace skills automatically. Give the agent the canonical skill and `knowledge/index.md`, or explicitly ask it to read MCP resources `aurora://instructions`, `aurora://workflow-routing`, `aurora://evidence`, then use `knowledge_read`/`knowledge_search`. These resources read the exact canonical files; they are not divergent workflow copies. If a host cannot consume resources, paste the canonical instructions into its instruction context. Give it the same first prompt from the README and verify actual tool calls.

### ChatGPT and other GPT hosts

“GPT-based” describes a model, not an execution interface. **Codex CLI/IDE with local stdio** is the documented OpenAI route here. A custom local agent runtime can spawn the same stdio launcher and supply the canonical instructions/OKF resources, but that integration must be tested separately.

Browser ChatGPT cannot launch this repository's stdio command on a colleague's machine. A ChatGPT MCP app/plugin requires a reachable remote MCP interface (for example Streamable HTTP over HTTPS) and a deployment/authentication/access arrangement; this repository currently ships **stdio only**, no remote endpoint, connector manifest or tunnel integration. The operator would need to supply and secure that bridge and retain the terminal approval mechanism on the execution host. Installing an OKF bundle or pasting a branch URL does not provide local tool execution. See the [official ChatGPT MCP quickstart](https://developers.openai.com/plugins/build/app-quickstart) for its separate interface requirements. No browser ChatGPT interoperability test is claimed.

## Inspect, plan, authorize, execute

The agent starts with MCP `inspect_environment`, `inspect_assets`, `list_runs`; validates the selected recipe/head; then calls `plan_execution`. Reuse existing compatible artifacts before downloads or training. Four recipe IDs are `cpu-smoke-v1`, `real-gpu-v1`, `no2-us-west-v1`, `o3-global-v1`.

Use one of these four canonical refinement selections, or `none`:

| Human choice | `head` value |
| --- | --- |
| Flow matching with UNet | `flow_matching_conv_unet` |
| Flow matching with Transformer | `flow_matching_transformer` |
| Diffusion with UNet | `diffusion_unet` |
| Diffusion with Transformer | `diffusion_transformer` |

`flow_matching_unet` is the historical adapter, not an alias for the unified convolutional UNet. The common modes are `replay`, `resume`, `warm-start`, `reproduce`, `evaluate`; exact checkpoint requirements differ. Replay never silently creates a newly trained model. A requested `product: ensemble` needs at least two members and a compatible stochastic configuration; canonical point inference remains deterministic and spatial-only. For historical combined checkpoints, choose `no2-historical-forecast-forced-v1` or `o3-historical-forecast-forced-v1` only when their recorded exogenous-input contract matches. The historical-named variants reuse source forcing dynamics with specified-cycle CAMS forecasts, excluding unavailable future analyses. They are a versioned approximation to the old analysis-refresh behavior: checkpoint-head replay may be compatible while the baseline is shifted. Neither these variants nor the canonical autonomous recipes establish exact historical numerical reproduction. Identify flow versus diffusion from checkpoint/configuration metadata, not the word “Transformer”.

For an agent, use MCP. The following **human terminal** examples show the shared backend and inspect plans without executing them. Set these paths from `setup_status` (or use your manual checkout/environment); direct module commands need the source on their import path:

```bash
export PYTHONPATH="/absolute/path/to/plugin-or-checkout"
WORKFLOW_PYTHON="/absolute/path/to/selected-environment/bin/python"
WORKFLOW_CONFIG="/absolute/path/to/workflow.json"
"$WORKFLOW_PYTHON" -m aurora_workflow --config "$WORKFLOW_CONFIG" plan --recipe cpu-smoke-v1 --head flow_matching_conv_unet --mode reproduce --case-id smoke-flow-unet
"$WORKFLOW_PYTHON" -m aurora_workflow --config "$WORKFLOW_CONFIG" plan --recipe cpu-smoke-v1 --head flow_matching_transformer --mode reproduce --case-id smoke-flow-transformer
"$WORKFLOW_PYTHON" -m aurora_workflow --config "$WORKFLOW_CONFIG" plan --recipe cpu-smoke-v1 --head diffusion_unet --mode reproduce --case-id smoke-diffusion-unet
"$WORKFLOW_PYTHON" -m aurora_workflow --config "$WORKFLOW_CONFIG" plan --recipe cpu-smoke-v1 --head diffusion_transformer --mode reproduce --case-id smoke-diffusion-transformer
```

For a real NO2 plan, replace the recipe with `no2-us-west-v1`; for O3 use `o3-global-v1`. Bound time, disk, download bytes, requests, steps, epochs, cases, memory, device and ensemble members in a local JSON request passed with `plan --request /absolute/path/request.json`. This is a typed `PlanRequest`, for example:

```json
{
  "recipe": "no2-us-west-v1",
  "head": "flow_matching_transformer",
  "mode": "replay",
  "case_id": "no2-replay-flow-transformer",
  "product": "point",
  "seed": 42,
  "inputs": {
    "pretrained": "/absolute/path/assets/aurora-0.4-air-pollution.ckpt",
    "static": "/absolute/path/assets/aurora-0.4-air-pollution-static.npz",
    "refinement": "/absolute/path/assets/trained-refinement.ckpt"
  },
  "limits": {
    "max_wall_seconds": 7200,
    "max_download_bytes": 0,
    "max_requests": 0,
    "gpu_count": 1,
    "device": "cuda:0"
  }
}
```

Paths must be under configured permitted roots; the trained checkpoint must carry the expected compatibility metadata. The static NPZ is the numerical representation produced by the approved asset tool from the exact official pickle, with its checksum/provenance sidecar. Do not rename or deserialize an arbitrary pickle. This request deliberately does not authorize downloads; missing prepared data/baseline/reference will appear as plan prerequisites. Use `real-gpu-v1` for the bounded acquisition-through-evaluation integration recipe and inspect its actual storage/request bounds before approval. Historical production dates, target levels, complete backbone fields and changes from old exogenous-input behavior are in recipes and the workflow inventory; do not overwrite them with slide assumptions.

The operator reviews the returned plan hash, resource limits, costs/unknowns, input fingerprints and stage list, then approves that plan in their own interactive terminal:

```bash
/absolute/path/aurora/bin/aurora-mcp --approve PLAN_ID
```

No MCP tool approves a plan, and a model-authored `approved=true` is not authorization. Do not have the agent automate the terminal confirmation or call internal approval methods. Approval uses local HMAC state and is tied to the effective plan and inputs; this protects the MCP capability boundary, not against the machine owner or an agent separately granted unrestricted local shell access. Configure client permissions accordingly.

After approval, the agent can invoke MCP `execute_workflow` for the full approved chain or the explicitly planned individual stage tools. Long operations return a durable job ID. A human can use `execute PLAN_ID`, `status JOB_ID`, `logs JOB_ID`, `cancel JOB_ID`, or `recover JOB_ID` through the same CLI. Do not repeat individual approval requests for unchanged stages. Changed code/configuration/input hashes or bounds require a new plan. Recovery reuses supported persisted artifacts/state within the original budget; incompatible or missing evidence remains blocked.

## Read results and knowledge

Inspect `metrics.json`, the SVG plot, Markdown evaluation summary, manifests and evaluation receipt under the configured run output. Baseline fields remain separately available. Evaluate identical cases/coordinates/units/masks, report exclusions, and distinguish deterministic points from stochastic members and ensemble statistics. Positive error improvement is `100*(baseline-refined)/baseline`; negative means worse. CAMS operational reference agreement is not independent observational validation.

Run `knowledge_validate` through MCP (or human CLI `knowledge-validate`). Search/read accept `scope: "bundle"` for committed concepts or `scope: "runs"` for the runtime overlay. They use offline Markdown; no database, embedding service or paid API is needed. `knowledge_refresh` previews index changes without mutating the bundled documents; the controlled local helper can apply them. `knowledge_register` verifies a successful scientific run's artifact hashes (metadata/report-only jobs do not count) and writes a compact concept to the runtime knowledge overlay, retaining receipts outside committed knowledge. Never label synthetic smoke metrics, historical prose or an unavailable presentation as new real-data evidence.

Default validation is `python -m pytest --confcutdir=tests/workflow tests/workflow`, without large downloads/private credentials. Opt-in real GPU testing is explicitly gated by local resources and the documented test configuration; skips/blockers must retain their reason. Check the implementation report for exactly which tests and client sessions actually ran.

Reference revisions and accessed-page hashes are in [provenance/references.json](../provenance/references.json). They record documentation research, not an assertion that every upstream page is immutable.
