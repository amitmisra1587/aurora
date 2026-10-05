# Claude Code plugin runbook

This plugin packages the existing `aurora_workflow` backend and the canonical
air-pollution instructions. It does not replace the Aurora science code. The
branch already contains CAMS planning/acquisition, full-backbone preparation,
the frozen `AuroraAirPollution` rollout, four residual heads, durable approved
jobs, evaluation and provenance. The plugin adds Claude Code manifests,
focused skills, a launcher and container packaging.

## Recommended install: branch clone, configure, install

Use Python 3.12–3.14 and Git. Linux is the supported worker platform. This
branch is not the repository default branch, so always select it explicitly.
From a shell:

```bash
git clone --branch agent_skills_to_finetune_aurora --single-branch \
  https://github.com/midatm1234/aurora.git aurora-plugin
cd aurora-plugin

WORKFLOW_VENV="${XDG_CACHE_HOME:-$HOME/.cache}/aurora-air-pollution/venv"
WORKFLOW_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/aurora/workflow.json"
WORKSPACE="$HOME/aurora-air-pollution-work"

python3.12 scripts/bootstrap_workflow.py --venv "$WORKFLOW_VENV" --data
"$WORKFLOW_VENV/bin/python" -m aurora_workflow --config "$WORKFLOW_CONFIG" \
  configure --workspace "$WORKSPACE"
AURORA_WORKFLOW_VENV="$WORKFLOW_VENV" AURORA_WORKFLOW_CONFIG="$WORKFLOW_CONFIG" \
  bin/aurora-mcp --check

claude plugin validate .
claude plugin marketplace add .
claude plugin install aurora-air-pollution@aurora
claude plugin list
```

`--data` installs pinned MCP, CAMS and preparation dependencies without
installing PyTorch. The environment and configuration live outside the plugin
checkout/cache. Bootstrap is repeatable for its own matching, marked
environment; it refuses to mutate an unrelated or differently pinned
environment. The configure command refuses to overwrite an existing config.
`--check` runs the backend doctor without downloading assets or loading the
model.

Claude Code's current official marketplace instructions support a branch ref
on the GitHub marketplace source. After setting up the external environment
from the clone above, the equivalent remote-source commands are:

```bash
claude plugin marketplace add midatm1234/aurora#agent_skills_to_finetune_aurora
claude plugin install aurora-air-pollution@aurora
```

The `#branch` form is documented at
[Host and maintain a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace#pin-a-branch-or-tag).
The clone commands above are the reliable fallback and also allow local
validation. No Claude Code binary was available in this implementation
environment, so client-side validation/session startup is not claimed.

After installation, start a new Claude Code session or reload plugins. Confirm
the component list with `claude plugin details aurora-air-pollution`; skills
appear as `/aurora-air-pollution:aurora-setup`,
`/aurora-air-pollution:aurora-cams-data`,
`/aurora-air-pollution:aurora-finetune`,
`/aurora-air-pollution:aurora-evaluate`, and
`/aurora-air-pollution:aurora-reproduce`. The bundled MCP server starts from
the plugin's `${CLAUDE_PLUGIN_ROOT}/bin/aurora-mcp` path, not from a hard-coded
checkout path. It reads the default external config and environment documented
below. The server writes only MCP protocol messages to stdout and logs to
stderr.

## Native setup, assets and secure ADS access

The default locations are:

- Python environment: `${XDG_CACHE_HOME:-~/.cache}/aurora-air-pollution/venv`
- Local settings: `${XDG_CONFIG_HOME:-~/.config}/aurora/workflow.json`
- Data, cache, outputs and durable job/approval state: separate subdirectories
  below the workspace passed to `configure`
- ADS credentials: `~/.cdsapirc`, or the path in `CDSAPI_RC`

Keep credentials, configs, caches, data, checkpoints and job outputs outside
the versioned plugin and plugin cache. Use a dedicated workspace; point
`read_roots`/asset paths at existing trusted artifacts when reusing them.
Never paste a token into chat, a recipe, a log or a report.

Create an ADS account, generate a personal access token in the ADS profile, and
manually accept the CAMS dataset terms in the browser before requesting data.
Put the token only into your local file, using the format given by the current
[ADS API setup page](https://ads.atmosphere.copernicus.eu/how-to-api):

```yaml
url: https://ads.atmosphere.copernicus.eu/api
key: <enter-your-token-locally>
```

```bash
chmod 600 "${CDSAPI_RC:-$HOME/.cdsapirc}"
bin/aurora-mcp --check
```

The doctor reports presence only. It does not prove that ADS permissions,
accepted terms or product availability are valid. An acquisition fails clearly
when no local credentials are present; API-side terms/date/variable errors are
not converted into success. The `cdsapi` client remains supported by the ADS
setup guidance; this branch pins its compatible client and the verified
dataset form/request fields in the shared backend.

For only MCP/setup/recipe inspection, a separate minimal environment is
available:

```bash
python3.12 scripts/bootstrap_workflow.py --venv "$HOME/.cache/aurora-inspect/venv"
```

For the CPU fixture suite, use a different path and install the CPU science
stack. This does not install CUDA:

```bash
python3.12 scripts/bootstrap_workflow.py --venv "$HOME/.cache/aurora-science-cpu/venv" --science
"$HOME/.cache/aurora-science-cpu/venv/bin/python" -m pytest \
  --confcutdir=tests/workflow tests/workflow
```

For real GPU training/inference, use a compatible CUDA-enabled PyTorch
environment and check `doctor --check-torch`; do not replace the fork with a
PyPI/weather starter package. Public pinned backbone weights and static assets
are retrieved only through a bounded approved plan. Historical trained
refinement checkpoints are not included; replay requires a trusted compatible
checkpoint supplied by the operator.

## One bounded first run

First confirm basic MCP operation without external data. With the plugin
connected, call `inspect_environment`, `inspect_assets`, `list_runs`, then
`validate_recipe` for `cpu-smoke-v1`. Call `plan_execution` with
`{"recipe":"cpu-smoke-v1","head":"flow_matching_transformer","mode":"reproduce","case_id":"cpu-smoke-flow-transformer"}`.
Review the returned plan and approve it in a human terminal; only then call
`execute_workflow` with that `plan_id`. Monitor `job_status` and bounded
`job_logs`. This fixture exercises the workflow plumbing and existing head
implementation; it is synthetic, not a forecast-skill result.

To plan a bounded first regional CAMS download, use the versioned
`no2-us-west-v1` recipe and keep the selected target/domain/levels from the
recipe:

```json
{
  "request": {
    "recipe": "no2-us-west-v1",
    "head": "none",
    "mode": "reproduce",
    "case_id": "no2-cams-one-cycle",
    "data": {
      "cycles": ["2024-07-01T12:00:00"],
      "lead_hours": [12],
      "target_variables": ["no2", "tcno2"],
      "target_levels": [1000, 925, 850]
    },
    "limits": {
      "device": "cpu",
      "gpu_count": 0,
      "max_requests": 3,
      "max_download_bytes": 2147483648,
      "max_disk_bytes": 4294967296,
      "max_wall_seconds": 3600
    },
    "stages": ["sources", "acquire", "prepare"]
  }
}
```

This is a *planning request*, not an executed result. The MCP server calculates
the exact requests and byte estimate from the current recipe/backend. It must
include both initialization history times, all backbone input fields and the
selected target reference; the recipe's regional target domain does not shrink
the global backbone history. If the plan reports more requests/bytes or
blockers than the limits allow, do not loosen limits automatically: revise and
review a new plan. The operator approves once in the terminal, then the agent
executes the approved stages through MCP. Expected data artifacts include
per-request atomic receipts and checksums, prepared cycle/lead/valid-time
NetCDF files, and a run manifest. A later separate recipe plan is needed for
weights, baseline, training/inference and evaluation. Do not label either this
download or the synthetic smoke as an end-to-end real-data reproduction.

## Recipes, heads and workflow modes

The canonical portable recipes are pinned spatial-only snapshots:

| Workflow | Recipe | Default head |
|---|---|---|
| Regional western-US NO2/tcNO2 | `no2-us-west-v1` | `flow_matching_transformer` |
| Global ozone | `o3-global-v1` | `flow_matching_conv_unet` |

The four unified refinement selections are
`flow_matching_conv_unet`, `flow_matching_transformer`, `diffusion_unet`, and
`diffusion_transformer`. `flow_matching_unet` retains its distinct historical
adapter meaning; it is not an alias for the unified convolutional UNet.
`none` leaves the deterministic baseline unchanged.

Use the exact mode:

- `replay`: requires an identified compatible trained checkpoint; never trains.
- `resume`: requires full compatible training state supported by the backend.
- `warm-start`: starts a new experiment from compatible weights; not optimizer
  continuation.
- `reproduce`: trains a new experiment under the recipe and approved bounds.
- `evaluate`: reuses matched artifacts and does not train.

The baseline stays frozen and refined fields are never fed back into it.
Point output is a deterministic product; a stochastic ensemble is a separate
requested product with its own member count/seed. Historical forecast-forced
recipes remain separate from canonical autonomous recipes. Do not change YAML
scientific settings to make assets appear compatible.

## Progress, recovery and output

The recommended chain is `inspect_environment`, `inspect_assets`, `list_runs`,
`validate_recipe`, `plan_execution`, operator approval, one `execute_workflow`,
then `job_status`/bounded `job_logs`. Jobs, plans, approval state and stage
receipts are persisted below `state_root`. Reconnection does not submit another
job. `recover_job` is for supported interrupted jobs with the same plan and
inputs; changed code/config/data/resource limits require a new plan. `cancel_job`
terminates the active attempt; do not submit a duplicate to evade a bound.

Run outputs are under `output_root/<run-id>/`, including a run manifest and
stage receipts. Successful evaluation produces `metrics.json`,
`metrics.svg`, `evaluation.md`, coverage/exclusion details and checksummed
artifacts. Reports compare matched samples in physical units; negative
improvement is retained. CAMS is an operational model reference, not
independent observational validation. Missing unpublished checkpoints are
reported as `requires_artifact`, not replaced with new training.

## Docker

Docker uses the same `aurora_workflow` backend. It does not download data,
weights or checkpoints during image build, and it receives no credentials
unless mounted at runtime. The CPU and CUDA targets use a patch-pinned Python
base / an existing Aurora NGC PyTorch release and the exact dependency pins in
`requirements/`; rebuild and review those pins as one change when updating.
`--init` forwards signals/reaps the worker. The default stdio run is
non-interactive (`-i`, no `-t`).

Build from the clean branch checkout:

```bash
docker build -f Dockerfile.workflow --target cpu -t aurora-air-pollution:cpu .
# Optional NVIDIA image; see prerequisites below.
docker build -f Dockerfile.workflow --target cuda -t aurora-air-pollution:cuda .
```

The Docker-backed launcher maps one host workspace to `/workspace`, mounts the
container-path settings read-only, and optionally mounts the ADS credentials
read-only. Initialize the container config once using the CPU image; the
settings then refer to the mounted `/workspace/{data,cache,runs,state}` paths:

```bash
WORKSPACE="$HOME/aurora-air-pollution-docker"
CONFIG="$HOME/.config/aurora/workflow-container.json"
mkdir -p "$WORKSPACE" "$(dirname "$CONFIG")"
docker run --rm --init --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$WORKSPACE,dst=/workspace" \
  --mount "type=bind,src=$(dirname "$CONFIG"),dst=/config" \
  --entrypoint python aurora-air-pollution:cpu \
  -m aurora_workflow --config /config/workflow-container.json \
  configure --workspace /workspace
```

Set the following in the environment that launches Claude Code, then start a
new session. These select container mode for the plugin's single bundled MCP
server; do not also add a second Docker MCP server:

```bash
export AURORA_WORKFLOW_DOCKER_IMAGE=aurora-air-pollution:cpu
export AURORA_WORKFLOW_DOCKER_CONFIG="$CONFIG"
export AURORA_WORKSPACE="$WORKSPACE"
```

For CAMS access, the launcher uses `${CDSAPI_RC:-~/.cdsapirc}` on the host and
mounts it read-only in the container. It maps MCP job state and outputs to the
same persistent host workspace. Approvals must use the same image/config and
state volume (paths inside the config are container paths); run the approval
command as a separate interactive container:

```bash
docker run --rm -it --init --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$WORKSPACE,dst=/workspace" \
  --mount "type=bind,src=$(dirname "$CONFIG"),dst=/config" \
  --entrypoint python aurora-air-pollution:cpu \
  -m aurora_workflow --config /config/workflow-container.json approve PLAN_ID
```

The installed plugin stores its launcher/dependencies outside the image, while
the image contains a snapshot of this branch's code. Rebuild the image when
updating the checkout and keep the plugin/image versions aligned. If MCP or the
container stops during a worker, the persistent state may mark the job
interrupted; reconnect, inspect status/logs, and recover only through the
backend. Do not mount the Docker socket or run privileged.

CUDA requires an NVIDIA GPU, compatible host NVIDIA driver, NVIDIA Container
Toolkit/runtime, and enough device memory for the exact approved plan.
Installing Docker does not provide a GPU or CUDA training on non-NVIDIA
hardware. No universal GPU-memory minimum is claimed; the doctor and reviewed
plan report local resources and checkpoint/config compatibility.

### Platform support and validation status

| Host | MCP/setup/data path | Real CUDA science | Status in this branch |
|---|---|---|---|
| Linux x86_64 CPU | Native or CPU Docker | No | CI covers CPU fixtures and MCP; Docker build unavailable in this environment |
| Linux x86_64 NVIDIA | Native CUDA PyTorch or CUDA Docker target | Yes, with compatible driver/toolkit and memory | Code path exists; no GPU execution claimed here |
| Windows | Use WSL2/Linux for workers | Only with a supported NVIDIA WSL2/container stack | Native Windows worker management is unsupported; WSL2 not tested here |
| macOS Intel/ARM | Docker Desktop CPU may be useful for metadata/data tasks | No NVIDIA CUDA path | Native worker management and ARM scientific stack unverified; no training claim |

No Docker daemon, compatible GPU, ADS account session or Claude Code client was
available for this implementation run. Image builds, GPU execution and
Claude/VS Code plugin loading are therefore explicitly unverified.

## Claude Desktop, Codex and Copilot

Claude Desktop is an MCP host, not a Claude Code plugin host. Clone the same
branch, bootstrap/configure as above, then register the local stdio launcher
using the Desktop MCP configuration format:

```json
{
  "mcpServers": {
    "aurora-air-pollution": {
      "command": "/absolute/path/aurora-plugin/bin/aurora-mcp",
      "args": [],
      "env": {
        "AURORA_WORKFLOW_VENV": "/absolute/path/to/aurora-air-pollution/venv",
        "AURORA_WORKFLOW_CONFIG": "/absolute/path/to/aurora/workflow.json"
      }
    }
  }
}
```

Use absolute paths, restart Desktop, and inspect its MCP tool list. Desktop
does not automatically discover Claude Code plugin skills; provide the
canonical workflow prompt from `.agents/skills/msresearch-aurora-air-pollution/SKILL.md`
or use Claude Code for skill discovery. For Docker, set the three Docker
environment variables above instead of adding another registration.

Codex and GitHub Copilot in VS Code retain their existing, client-specific
skill/MCP configuration formats. Use the Codex and VS Code examples in
`docs/agent-workflow.md`; do not copy Claude's `mcpServers` JSON into VS Code's
`servers` configuration.

When using this plugin in a checkout that also exposes the repository's
canonical `.claude/skills` adapter, invoke either the focused plugin skill or
the canonical repository skill as appropriate; do not add the separate
`claude mcp add aurora_air_pollution ...` server while the plugin's
`aurora-air-pollution` MCP server is enabled.

## Update, removal and tests

Update the branch-pinned marketplace/plugin with:

```bash
claude plugin marketplace update aurora
claude plugin update aurora-air-pollution@aurora
```

Remove the plugin with `claude plugin uninstall aurora-air-pollution@aurora`;
remove the marketplace only after its plugins are uninstalled. Keep the
external workspace, ADS config, assets and run state if you may need them
later; uninstalling the plugin does not make those artifacts part of Git.

Repeatable offline checks:

```bash
python -m pytest --confcutdir=tests/workflow tests/workflow
```

The test suite includes the actual MCP SDK stdio transport, skill/manifest/link
checks and mocked CAMS contracts. Real ADS acquisition, container builds,
Claude Code session/plugin discovery and GPU smoke runs are separately gated
and must not be inferred from those passing checks.
