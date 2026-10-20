# Claude Code plugin runbook

The [README](../README.md) is the short first-use route. This runbook covers path choices, larger environments, manual recovery and containers. One canonical [scientific skill](../.agents/skills/msresearch-aurora-air-pollution/SKILL.md), the [OKF bundle](../knowledge/index.md) and the existing `aurora_workflow` backend serve every client.

## Marketplace installation

Prerequisites: Git, Claude Code with plugin support/authentication, Python 3.12–3.14 with `venv` and `pip`, network access to the pinned packages and writable external storage. Python must be on the PATH inherited by the MCP client; an IDE started from a GUI may have a different PATH from your terminal.

**Terminal:**

```bash
claude plugin marketplace add "midatm1234/aurora#agent_skills_to_finetune_aurora"
claude plugin install aurora-air-pollution@aurora
claude plugin list
```

Restart the Claude session (including the VS Code extension session), then ask:

> Set up this machine for the Aurora air-pollution workflow. Check the environment, available compute, existing datasets, checkpoints, and previous outputs. Prepare the lightweight setup and explain which workflow steps this machine can run.

**Claude session:** inspect `/plugin`, `/mcp`, and `/aurora-air-pollution:aurora-setup`. The other skills are `aurora-cams-data`, `aurora-finetune`, `aurora-evaluate` and `aurora-reproduce`, under the same namespace. The plugin manifest's `mcpServers` field launches `${CLAUDE_PLUGIN_ROOT}/bin/aurora-mcp`. There is no root `.mcp.json` to create a duplicate project-scope registration when opening the checkout. Do not register a second `aurora_air_pollution` server when the plugin is active.

Marketplace name: `aurora`; plugin name: `aurora-air-pollution`; plugin version: `0.2.0`. The marketplace is fetched from the selected branch and the plugin entry's relative `./` source copies that same checkout, including hidden canonical instructions and knowledge. There is no independent fetch that could fall back to the default branch. See [official branch selection](https://code.claude.com/docs/en/plugins/host-marketplace) and [relative source semantics](https://code.claude.com/docs/en/plugins/marketplace-reference#relative-path-plugin-source). A local marketplace installation below uses the local source, allowing unpublished edits to be tested.

## First connection

The dependency-free supervisor answers MCP initialization immediately and exposes `setup_status` / `setup_retry`. In a background thread it:

1. Reads optional external launcher settings, selects/reuses a compatible environment, and takes an installation lock.
2. Installs only `requirements/workflow-light.txt` into an external environment if needed. It uses the packaged code directly through `PYTHONPATH`, so it does not need Git metadata, an editable package build or a writable plugin cache.
3. Creates the default workflow configuration only if absent and validates existing settings without overwriting them.
4. Starts the shared official-SDK stdio backend and announces a changed tool list. The two setup tools remain available alongside the 24 workflow tools.

Ask for `setup_status`, then `inspect_environment`, `inspect_assets`, `list_runs`, and `knowledge_validate`. Success: setup `ready`, `fork_import_verified: true`, your configured roots, empty assets/jobs on a fresh machine, and valid knowledge. Missing NumPy/PyTorch/data packages are normal in this minimal profile. If the host caches tool lists, restart the MCP server/session after setup completes.

All protocol traffic uses stdout; setup diagnostics use stderr, and package installation details go to a private external log whose path is reported by `setup_status`. Setup does not download scientific assets, datasets or credentials and does not approve or run a scientific plan. Setup success does not establish GPU readiness or forecast performance.

## Paths and environments

Defaults:

- Settings: `${XDG_CONFIG_HOME:-~/.config}/aurora/launcher.json` (optional).
- Workflow configuration: `${XDG_CONFIG_HOME:-~/.config}/aurora/workflow.json`.
- Minimal environment: `${XDG_CACHE_HOME:-~/.cache}/aurora-air-pollution/venv-<Python-major.minor>-<light-lock-hash>`.
- Workspace: `~/aurora-air-pollution-work`, with separate `data`, `cache`, `runs`, `state` roots.
- Setup log and lock: next to the selected environment, named `<venv-name>.setup.log` and `.setup.lock`.

To change paths, ask the setup agent to create/edit **this local configuration file**, before first connection if desired. Use your own absolute paths or `~/...`; no shell expansion occurs inside JSON except leading `~`:

```json
{
  "workspace": "~/aurora-air-pollution-work",
  "venv": "~/aurora-environments/mcp",
  "config": "~/.config/aurora/workflow.json"
}
```

Every key is optional. A custom `workspace` applies only when creating a missing workflow config. Existing `workflow.json` roots remain authoritative; inspect them before moving data. Set `read_roots` and checksum/architecture-bearing `assets` entries there to reuse trusted datasets, checkpoints and outputs on shared disks. Do not place mutable paths inside the installed plugin. No config or environment is overwritten to make it appear compatible.

Advanced environment overrides take precedence over launcher.json: `AURORA_WORKSPACE`, `AURORA_WORKFLOW_VENV`, `AURORA_WORKFLOW_CONFIG`; `AURORA_PYTHON` selects the bootstrap Python. Put overrides in the launching process or the host's MCP `env` object. Prefer launcher.json for persistent path choices. XDG variables change the default config/cache base directories.

A compatible existing environment must have Python 3.12–3.14 and the exact minimal package pins; it may also contain scientific packages. The legacy `~/.cache/aurora-air-pollution/venv` is reused if compatible. Explicit incompatible environments are preserved: choose a new path or deliberately prepare a compatible environment yourself. Default lock changes select a new path on update, leaving older environments and runs intact. Concurrent starts serialize installation; interrupted managed installations are retried.

### Larger dependencies, only when requested

Resolve `PLUGIN_ROOT` below to the installed skill's `../../` directory, or to your manual checkout. The setup agent already has that skill path; users need not search Claude's cache. These commands run in a **terminal** or through an agent acting on a request for that capability:

```bash
python3.12 "$PLUGIN_ROOT/scripts/bootstrap_workflow.py" \
  --venv "$HOME/aurora-environments/data" --data --no-project
# Optional CPU fixture / analysis environment; includes PyTorch, no CUDA:
python3.12 "$PLUGIN_ROOT/scripts/bootstrap_workflow.py" \
  --venv "$HOME/aurora-environments/science-cpu" --science --no-project
```

Use the supported Python executable available on your machine (`python3.12`, `python3.13` or `python3.14`). Each bootstrap profile has its own marker; create a separate environment when changing profiles instead of mutating one used by active jobs. Set `venv` in launcher.json to the chosen environment and reconnect. The launcher keeps imports tied to the current installed source even when a dependency environment is reused.

For CUDA training/inference, supply a compatible Linux CUDA-enabled scientific environment with the light/data requirements and the existing `finetune` dependencies. The CPU bootstrap does not install CUDA. Select it with launcher.json; call `inspect_environment(check_torch=true)` and check the actual device/memory and recipe/checkpoint contracts. No GPU minimum or automatic CUDA installation is promised.

### ADS access

For a requested CAMS acquisition, create your own ADS account and manually accept the selected dataset terms. Follow the current [ADS API setup](https://ads.atmosphere.copernicus.eu/how-to-api). Enter the token locally in `~/.cdsapirc` or `CDSAPI_RC`, never in chat, recipes or reports:

```yaml
url: https://ads.atmosphere.copernicus.eu/api
key: <enter-your-token-locally>
```

**Terminal:** `chmod 600 "${CDSAPI_RC:-$HOME/.cdsapirc}"`. Inspection reports presence only; it does not establish accepted terms or product/date access. Public model/static files are retrieved only by a bounded approved plan. Unpublished refinement checkpoints must be supplied as trusted compatible artifacts by the operator.

## Manual fallback

Use this when you prefer a checkout, a client cannot install plugins, or initial MCP connectivity fails. **Terminal:**

```bash
git clone --branch agent_skills_to_finetune_aurora --single-branch \
  https://github.com/midatm1234/aurora.git aurora-plugin
cd aurora-plugin
bin/aurora-mcp --check
claude plugin validate .
claude plugin marketplace add .
claude plugin install aurora-air-pollution@aurora
```

Use either the local marketplace or the remote marketplace for `aurora`; inspect an existing registration before replacing it. `--check` performs repeatable minimal setup and prints doctor JSON; `--install` prepares setup and prints paths; neither starts a scientific job. Plain `bin/aurora-mcp` serves stdio. Both work from an unrelated working directory. To select one custom workflow config directly, use `bin/aurora-mcp --config /absolute/path/workflow.json`.

If an existing manually managed environment is desired, use `scripts/bootstrap_workflow.py --venv /external/path --no-project`, then choose it in launcher.json. This works without a package build; if using `python -m aurora_workflow` directly outside the checkout, set `PYTHONPATH` to that checkout. Prefer the launcher, which supplies the correct import path automatically.

| Symptom | Recovery |
| --- | --- |
| MCP cannot start, Python error in client logs | Install Python 3.12–3.14 with venv/pip (on Debian/Ubuntu the matching `python3.x-venv` package may be needed). Make it visible to the client or set `AURORA_PYTHON`; restart the client. |
| Setup `installing` | Poll `setup_status`; inspect the reported private pip log locally. |
| Setup `failed`, dependency installation | Restore package-index/network access or venv/pip support. Call `setup_retry` or rerun `--check`. |
| Incompatible existing environment | Preserve it; choose a new external `venv` path, then retry. |
| Invalid launcher/workflow config | Correct JSON and supported keys/absolute dedicated roots; keep state separate. Retry; existing settings are retained. |
| Ready but inspection tools missing | Reconnect/restart the MCP server to refresh the client's tool list. |
| Two Aurora servers | Disable the manual registration when using the plugin. |
| Old plugin after update | Update marketplace and plugin, verify installed version, restart the session; see below. |

For scientific approval, the agent reports the resolved launcher path. The **human runs in their own interactive terminal**:

```bash
"$PLUGIN_ROOT/bin/aurora-mcp" --approve PLAN_ID
```

This uses the same environment/config as MCP. Never ask the agent to automate approval. For custom per-registration environment overrides, apply the same overrides to this human command. The plain CLI approval example in the portable guide is also available.

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

## Platforms

| Machine | Intended capability | Actual validation |
| --- | --- | --- |
| Linux x86_64 CPU | Setup, metadata/OKF/recipe inspection; data/analysis after explicit dependencies | Clean setup, official SDK and CPU suite tested; see validation record |
| Linux x86_64 NVIDIA | Real baseline/refinement with compatible CUDA and memory | Existing code path; no GPU execution in onboarding validation |
| macOS Intel/ARM | Intended lightweight setup/inspection and compatible CPU analysis; remote Linux for CUDA | No Mac test; native worker lifecycle and scientific wheels unverified |
| Windows | Use WSL2/Linux environment for launcher/workers | Native Windows unsupported; WSL2 untested |
| Docker | CPU metadata/data or Linux CUDA image | Docker build/runtime not exercised here |

Do not infer Mac CUDA support from Claude Code supporting macOS. To run on a remote machine, install and start the agent/MCP there (for example VS Code Remote SSH); local Mac stdio cannot access the remote filesystem or GPU automatically. [Other hosts](agent-workflow.md#client-setup).

## Updates and removal

**Terminal:**

```bash
claude plugin marketplace update aurora
claude plugin update aurora-air-pollution@aurora
claude plugin list
```

Restart the session; inspect `/plugin` and `/mcp` again. This release bumps `0.1.0` to `0.2.0`; maintainers must bump `.claude-plugin/plugin.json` on subsequent published changes so cached installs refresh. The relative plugin source stays on the marketplace branch. A default dependency lock change gets its own external environment; an explicit environment path needs a compatible environment. Never update source/configuration beneath an active scientific job: input fingerprints and approvals must remain stable.

`claude plugin uninstall aurora-air-pollution@aurora` removes the plugin registration. External settings, environments, credentials and workspace persist; deleting scientific data is a separate user action.

[Onboarding validation](onboarding-validation.md) records versions, performed checks and exact untested client-session steps. [Portable agent guide](agent-workflow.md) covers Codex, Copilot, Desktop and GPT hosts. [Scientific implementation report](workflow-implementation-report.md) retains the earlier scientific validation record.
