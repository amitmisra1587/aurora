---
name: aurora-reproduce
description: Orchestrate the versioned regional NO2/tcNO2 or global O3 CAMS-to-AuroraAirPollution workflow from inspection and planning through evaluation and provenance. Use when asked for an end-to-end reproduction.
---

# Reproduce an Aurora air-pollution workflow

Read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md), [stage routing](../../.agents/skills/msresearch-aurora-air-pollution/references/workflow.md), [evidence rules](../../.agents/skills/msresearch-aurora-air-pollution/references/evidence.md), and [runbook](../../docs/claude-code-plugin.md).

1. Call `inspect_environment`, `inspect_assets`, and `list_runs` first. Reuse compatible local inputs, assets, baseline rollouts and checkpoints; inspect manifests and hashes.
2. Ask only for genuinely unresolved inputs: recipe (`no2-us-west-v1` or `o3-global-v1`), head (`none` or one of the four unified values), mode, product, case ID, and resource bounds. Use the recipe defaults unless an explicit change is part of the plan.
3. Call `validate_recipe`, then `plan_execution`. Present the effective config digest, input fingerprints, missing artifacts, ordered stages, CAMS request count/estimated bytes, disk/GPU/time/epoch limits and unknown costs. Never claim replay when the trained checkpoint is unavailable.
4. The operator approves this exact plan in their own local interactive terminal. Do not automate approval, invoke private approval methods, or bypass the plan with shell commands. After approval, call `execute_workflow` once; do not request per-stage approval again for unchanged inputs. A material change requires a new plan.
5. Track the durable job with `job_status` and bounded `job_logs`. Use `cancel_job` on request. Use `recover_job` only when backend status identifies an interrupted, supported job whose authorization and inputs are unchanged.
6. On successful completion, inspect the manifest, stage receipts, checksums, prepared data, baseline, refinement product, metrics and report. State whether the run used synthetic fixtures or real CAMS and compute; report blockers, negative metrics and exclusions. Do not call smoke completion scientific validation.
