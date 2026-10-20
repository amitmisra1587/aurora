# Aurora air-pollution workflow for your agent

Use this branch to prepare CAMS data, run the frozen `AuroraAirPollution` baseline, train or replay residual refinement, and evaluate matched forecasts on **your own compute**. It includes regional NO2/tcNO2 and global O3 recipes, durable jobs, artifact reuse and provenance. Existing scientific models and notebooks remain available.

Three components work together:

- **Skills** guide the agent through setup, data acquisition, refinement, evaluation and reproduction.
- **MCP server** supplies callable inspection and workflow tools on the machine where it runs.
- **Open Knowledge Format (OKF) bundle** carries portable workflow knowledge, references and constraints in [knowledge/](knowledge/index.md). Knowledge, skill discovery and tool connectivity are separate capabilities.

## Prerequisites

- Claude Code with plugin support and an authenticated account; Git.
- Python **3.12–3.14**, including `venv` and `pip`, visible to the client, and internet access for the small pinned MCP dependencies.
- A writable home directory (or your own external paths). No GPU, CAMS credentials, datasets or checkpoints are needed for first setup.

Linux x86_64 is tested for onboarding and CPU workflow checks. A Mac can use the intended lightweight inspection/knowledge route and analyze compatible outputs after installing analysis dependencies; **macOS has not been tested here**. Real training/inference uses a Linux NVIDIA/CUDA environment with sufficient memory. Use a remote Linux machine for that work from a Mac; the MCP process and files must be on that machine. Native Windows workers are unsupported; WSL2/Linux is the intended, untested route. See [platform details](docs/claude-code-plugin.md#platforms).

## Install in Claude Code

**Run in a terminal:**

```bash
claude plugin marketplace add "midatm1234/aurora#agent_skills_to_finetune_aurora"
claude plugin install aurora-air-pollution@aurora
```

Start a new Claude Code session, or reload its plugins, and ask:

> Set up this machine for the Aurora air-pollution workflow. Check the environment, available compute, existing datasets, checkpoints, and previous outputs. Prepare the lightweight setup and explain which workflow steps this machine can run.

The launcher connects immediately with `setup_status` while preparing its minimal environment and default configuration outside the installed plugin. It reuses compatible environments and preserves existing settings. PyTorch, CAMS data packages, weights and datasets are deferred until you request those capabilities. You do not need to clone the repository or find Claude's plugin cache.

**Confirm in the Claude Code session:** `/plugin` shows `aurora-air-pollution@aurora`; `/aurora-air-pollution:aurora-setup` is available; `/mcp` shows the bundled server connected. Ask the agent to call `setup_status`, then `inspect_environment`, `inspect_assets` and `list_runs`. Successful lightweight setup means `setup_status.state` is `ready`, inspection verifies this fork and reports your paths, and empty assets/runs are handled normally. Missing scientific packages are expected. If a client does not refresh tools after setup, reconnect the server or restart the session.

The marketplace source selects the named branch; its plugin source is `./`, relative to that same branch checkout. There is no second unpinned repository fetch. The Claude Code VS Code extension shares CLI plugin installations; restart its session after installing. [Detailed setup and recovery](docs/claude-code-plugin.md).

## Other agents

For the checkout-based routes below, **run in a terminal**, then open that directory in the client:

```bash
git clone --branch agent_skills_to_finetune_aurora --single-branch \
  https://github.com/midatm1234/aurora.git
cd aurora
bin/aurora-mcp --check
```

| Client | Installation | Skill entry point | MCP setup | Validation |
| --- | --- | --- | --- | --- |
| Claude Code CLI / VS Code extension | Marketplace above | Five namespaced `aurora-*` skills | Bundled plugin-manifest registration | CLI install and actual VS Code extension activation/inventory tested; authenticated chat untested |
| Codex CLI / IDE extension | Open branch checkout | `.agents/skills/` and `AGENTS.md` | `codex mcp add aurora_air_pollution -- /absolute/path/aurora/bin/aurora-mcp` | CLI registration and SDK tests; IDE session untested |
| GitHub Copilot, VS Code agent mode | Open branch checkout | `.agents/skills/`, `.github/copilot-instructions.md` | Copy [VS Code example](docs/clients/vscode-mcp.example.json) into `.vscode/mcp.json`; **MCP: List Servers** | Actual VS Code skill discovery and MCP calls tested; Copilot chat session untested |
| Claude Desktop / other local MCP hosts | Branch checkout | Read `aurora://instructions` resource or supply canonical skill | [Local stdio example](docs/clients/claude-mcp.example.json), with absolute launcher path | SDK/resources tested; Desktop session untested |
| ChatGPT / other GPT hosts | A host with access to the same execution machine | Explicit canonical instructions and OKF access | Local stdio-capable runtime, e.g. Codex; browser ChatGPT requires an additional remote transport/deployment | No bundled ChatGPT connector or HTTP server; [limitations](docs/agent-workflow.md#chatgpt-and-other-gpt-hosts) |

[Client instructions, schemas and exact remaining checks](docs/agent-workflow.md#client-setup). Copilot CLI and GitHub cloud agents have different setup and resource requirements; VS Code configuration does not register their tools.

## Common prompts

- **New machine:** “Inspect this machine and existing Aurora data, assets and runs. Prepare lightweight setup and explain which capabilities are ready and which dependencies are missing.”
- **Existing results:** “Analyze my existing Aurora outputs in `<path>` without training. Check manifests and matched samples, summarize metrics and plots, and retain negative results.”
- **CAMS download:** “Prepare a bounded CAMS download plan for `no2-us-west-v1` over `<UTC dates>`. Check existing data, full backbone history, credentials presence, request count, bytes, storage and time limits. Show the plan before execution.”
- **Baseline and refinement:** “Plan the Aurora baseline and `flow_matching_transformer` refinement for `no2-us-west-v1` on my available compute. Reuse verified assets; show GPU, time, storage and training bounds for terminal approval.” Other unified heads: `flow_matching_conv_unet`, `diffusion_unet`, `diffusion_transformer`; `none` preserves the baseline.
- **Evaluation:** “Evaluate these baseline and refined forecasts against the same matched CAMS reference. Compare by variable, pressure level and forecast lead time in physical units, with coverage, exclusions, plots and provenance. Do not train.”
- **Resume or reproduce:** “Inspect run `<run ID/path>` and its artifacts. Determine whether its checkpoint supports replay or full optimizer resume, or whether I need a new reproduction run. Preserve the recorded head, forcing contract and bounds; report missing artifacts.”

Inspection and knowledge navigation run on CPU. Data acquisition/preparation needs additional data packages; CAMS downloads also require your ADS account, local credentials and accepted dataset terms. Evaluation of existing compatible arrays runs on CPU with scientific dependencies. Real baseline/refinement computation needs the appropriate scientific environment, model assets and Linux CUDA resources; historical replay additionally needs the original compatible refinement checkpoint. Sharing this branch does not share unpublished checkpoints.

Scientific execution follows inspect → validate → bounded plan → **human terminal approval** → execute → evaluate/report. Setup success is not reproduction. Synthetic CPU checks establish workflow plumbing, not forecast performance; CAMS operational forecasts are a model reference, not observations.

## Your files

Defaults (XDG config/cache overrides are honored):

| Location | Contents |
| --- | --- |
| `~/.config/aurora/launcher.json` | Optional persistent `workspace`, `venv`, `config` path choices |
| `~/.config/aurora/workflow.json` | Validated local roots, permitted read roots and asset registry |
| `~/.cache/aurora-air-pollution/venv-<Python>-<lock>` | Minimal environment; dependency updates get a separate environment |
| `~/aurora-air-pollution-work/{data,cache,runs,state}` | Data, cached assets, outputs, jobs and approval state |
| `~/.cdsapirc` or `CDSAPI_RC` | Your local ADS credentials; never paste them into chat |

Ask the setup agent to inspect these paths before changing them. Reuse existing datasets/checkpoints through configured `read_roots` and asset records. A custom workflow configuration is preserved; its roots determine the actual data/output locations. [Path overrides and larger environments](docs/claude-code-plugin.md#paths-and-environments).

## Troubleshooting and updates

If the server is connected but workflow tools are absent, ask for `setup_status`: it reports progress, log location and recovery instructions. Fix package-index access or invalid local settings and call `setup_retry`; reconnect if necessary. If the server cannot connect at all, check Python 3.12–3.14 and `venv`/`pip` in the client's PATH, then restart the client. [Manual fallback and diagnostics](docs/claude-code-plugin.md#manual-fallback).

**Run in a terminal** to update:

```bash
claude plugin marketplace update aurora
claude plugin update aurora-air-pollution@aurora
```

Restart the session afterward. Plugin versions must increase when publishing changes so installed caches refresh. External settings, data and runs survive updates and uninstall.

More detail: [Claude runbook](docs/claude-code-plugin.md) · [other agents and workflow approval](docs/agent-workflow.md) · [onboarding validation](docs/onboarding-validation.md) · [scientific inventory](docs/workflow-inventory.md) · [scientific implementation report](docs/workflow-implementation-report.md) · [OKF knowledge](knowledge/index.md).

The upstream Aurora description, citation, examples and license follow. Its general weather example is separate from this branch's air-pollution workflow; use the workflow instructions above for CAMS and refinement work.

---

<img src="docs/gifs/high_res_2t.gif" alt="high resolution (0.1 degree) temperature at 2m predictions gif" width="150px">&nbsp;&nbsp;&nbsp;<img src="docs/gifs/no2.gif" alt="nitrogen dioxide predictions gif" width="150px">&nbsp;&nbsp;&nbsp;<img src="docs/gifs/wave_direction.gif" alt="ocean wave direction predictions gif" width="150px">&nbsp;&nbsp;&nbsp;<img src="docs/gifs/tc_tracks.gif" alt="tropical cyclone track predictions gif" width="220px">

# Aurora: A Foundation Model for the Earth System

[![CI](https://github.com/microsoft/Aurora/actions/workflows/ci.yaml/badge.svg)](https://github.com/microsoft/Aurora/actions/workflows/ci.yaml)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://microsoft.github.io/aurora)
[![Paper](https://img.shields.io/badge/arXiv-2405.13063-blue)](https://arxiv.org/abs/2405.13063)
[![DOI](https://zenodo.org/badge/828987595.svg)](https://doi.org/10.5281/zenodo.14983583)

Implementation of the Aurora model for Earth system forecasting.

[Link to the paper.](https://www.nature.com/articles/s41586-025-09005-y)

[Please see the documentation for detailed instructions and more examples.](https://microsoft.github.io/aurora)
You can also directly go to [a full-fledged example that runs the model on ERA5](https://microsoft.github.io/aurora/example_era5.html).

Cite us as follows:

```
@article{bodnar2025aurora,
    title = {A Foundation Model for the Earth System},
    author = {Cristian Bodnar and Wessel P. Bruinsma and Ana Lucic and Megan Stanley and Anna Allen and Johannes Brandstetter and Patrick Garvan and Maik Riechert and Jonathan A. Weyn and Haiyu Dong and Jayesh K. Gupta and Kit Thambiratnam and Alexander T. Archibald and Chun-Chieh Wu and Elizabeth Heider and Max Welling and Richard E. Turner and Paris Perdikaris},
    journal = {Nature},
    year = {2025},
    month = {May},
    day = {21},
    issn = {1476-4687},
    doi = {10.1038/s41586-025-09005-y},
    url = {https://doi.org/10.1038/s41586-025-09005-y},
}
```

Contents:

- [What is Aurora?](#what-is-aurora)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)
- [Security](#security)
- [Responsible AI Transparency Documentation](#responsible-ai-transparency-documentation)
- [Trademarks](#trademarks)
- [FAQ](#faq)

Please email [AIWeatherClimate@microsoft.com](mailto:AIWeatherClimate@microsoft.com)
if you are interested in using Aurora for commercial applications.
For research-related questions or technical support with the code here,
please [open an issue](https://github.com/microsoft/aurora/issues/new/choose)
or reach out to the authors of the paper.

## What is Aurora?

Aurora is a machine learning model that can predict atmospheric variables, such as temperature.
It is a _foundation model_, which means that it was first generally trained on a lot of data,
and then can be adapted to specialised atmospheric forecasting tasks with relatively little data.
We provide four such specialised versions:
one for medium-resolution weather prediction,
one for high-resolution weather prediction,
one for air pollution prediction,
and one for ocean wave prediction.

## Getting Started

Install with `pip`:

```bash
pip install microsoft-aurora
```

Or with `conda` / `mamba`:

```bash
mamba install microsoft-aurora -c conda-forge
```

Run the pretrained small model on random data:

```python
from datetime import datetime

import torch

from aurora import AuroraSmallPretrained, Batch, Metadata

model = AuroraSmallPretrained()
model.load_checkpoint()

batch = Batch(
    surf_vars={k: torch.randn(1, 2, 17, 32) for k in ("2t", "10u", "10v", "msl")},
    static_vars={k: torch.randn(17, 32) for k in ("lsm", "z", "slt")},
    atmos_vars={k: torch.randn(1, 2, 4, 17, 32) for k in ("z", "u", "v", "t", "q")},
    metadata=Metadata(
        lat=torch.linspace(90, -90, 17),
        lon=torch.linspace(0, 360, 32 + 1)[:-1],
        time=(datetime(2020, 6, 1, 12, 0),),
        atmos_levels=(100, 250, 500, 850),
    ),
)

prediction = model.forward(batch)

print(prediction.surf_vars["2t"])
```

Note that this will incur a 500 MB download.

Please read the [documentation](https://microsoft.github.io/aurora) for more detailed instructions and for which models are available.

For static-variable inspection/editing, see [`examples/static_variables_editor.ipynb`](examples/static_variables_editor.ipynb).
This notebook can help you visualise and modify existing static-variable arrays in a pickle file.
Adding a brand-new static variable and making Aurora consume that new variable in model inference is not available yet.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

See [`LICENSE.txt`](LICENSE.txt).

## Security

See [`SECURITY.md`](SECURITY.md).

## Responsible AI Transparency Documentation

An AI system includes not only the technology, but also the people who will use it, the people who will be affected by it, and the environment in which it is deployed.
Creating a system that is fit for its intended purpose requires an understanding of how the technology works, its capabilities and limitations, and how to achieve the best performance.
Microsoft has a broad effort to put our AI principles into practice.
To find out more, see [Responsible AI principles from Microsoft](https://www.microsoft.com/en-us/ai/responsible-ai).

### Use of this code
Our goal in publishing this code is
(1) to facilitate reproducibility of our paper and
(2) to support and accelerate further research into foundation model for atmospheric forecasting.
This code has not been developed nor tested for non-academic purposes and hence should only be used as such completely at your own risk.

### Intended use
Aurora is intended for medium- and high-resolution weather prediction, air pollution forecasting, ocean wave prediction, and global environmental modelling tasks.
The model can be adapted to specialised atmospheric forecasting tasks with relatively limited task-specific training data due to its foundation-model architecture.

### Out-of-scope use cases
Aurora is not designed or evaluated for direct operational decision-making without expert review, applications requiring guaranteed forecast accuracy, or non-environmental prediction tasks.
Use in safety-critical planning or automated decision pipelines should be accompanied by appropriate domain validation.

### Limitations
Although Aurora was trained to accurately predict future weather, air pollution, and ocean waves,
Aurora is based on neural networks, which means that there are no strict guarantees that predictions will always be accurate.
Altering the inputs, providing a sample that was not in the training set,
or even providing a sample that was in the training set but is simply unlucky may result in arbitrarily poor predictions.
In addition, even though Aurora was trained on a wide variety of data sets,
it is possible that Aurora inherits biases present in any one of those data sets.
A forecasting system like Aurora is only one piece of the puzzle in a weather prediction pipeline,
and its outputs are not meant to be directly used by people or businesses to plan their operations.
A series of additional verification tests are needed before it can become operationally useful.

In addition to the above, the models published here are streamlined versions of the models
originally developed internally.
Whereas we tried to be as thorough as possible, it is possible that the models published here
deviate from the original model in subtle, unintended ways.
This may affect predictive performance.

### Responsible AI considerations
Aurora is a research forecasting model and should not be treated as an operational weather service.
While the model can match or exceed traditional numerical baselines on established benchmarks,
its reliability can degrade in out-of-distribution conditions
(e.g., rare extremes, regime shifts, or regions/variables with limited historical fidelity in underlying reanalyses and simulations).
Outputs may also be misinterpreted if users overlook uncertainty, ensemble spread, or known limitations of the underlying training data.

The primary Responsible AI risks are
(1) unintended use by non-experts and
(2) downstream use in consequential decision-making without domain validation
(e.g., emergency response, critical infrastructure operations, safety-of-life planning).
To mitigate these risks, developers should:
clearly communicate that the release is for research evaluation and reproducibility;
require domain-expert review before any real-world decisions are informed by outputs;
implement basic input validation to ensure initial conditions come from credible sources
(e.g., established meteorological agencies and data providers);
and benchmark performance against accepted physical modelling systems for the specific geography, horizon, and variable(s) relevant to the intended application.

Aurora is best integrated as a decision-support component for expert analysis,
not as a fully autonomous trigger for actions.
For higher-risk scenarios, apply additional safeguards such as human-in-the-loop review,
conservative thresholds for alerts, calibration/verification tests,
and ongoing monitoring for drift when changing input sources or pre/post-processing.

### Data
The models included in the code have been trained on a variety of publicly available data.
A description of all data, including download links, can be found in [Supplementary C of the paper](https://arxiv.org/pdf/2405.13063).
The checkpoints include data from
ERA5, CMIP6 (CMCC-CM2-VHR4 and ECMWF-IFS-HR), HRES forecasts, GFS T0, GFS forecasts,
HRES T0,
HRES analysis,
HRES-WAM analysis,
CAMS reanalysis, and CAMS analysis.

### Evaluations
All versions of Aurora were extensively evaluated by evaluating predictions on data not seen during training.
These evaluations not only compare measures of accuracy, such as the root mean square error and anomaly correlation coefficient,
but also look at the behaviour in extreme situations, like extreme heat and cold, and rare events, like Storm Ciarán in 2023.
These evaluations are the main topic of [the paper](https://arxiv.org/pdf/2405.13063).

*Note: The documentation included in this file is for informational purposes only and is not intended to supersede the applicable license terms.*

## Trademarks

This project may contain trademarks or logos for projects, products, or services.
Authorized use of Microsoft trademarks or logos is subject to and must follow [Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

## FAQ

### How do I setup the repo for local development?

First, install the repository in editable mode and setup `pre-commit`:

```bash
make install
```

To run the tests and print coverage, run

```bash
make test
```

You can then explore the coverage in the browser by opening `htmlcov/index.html`.

To locally build the documentation, run

```bash
make docs
```

To locally view the documentation, open `docs/_build/index.html` in your browser.
