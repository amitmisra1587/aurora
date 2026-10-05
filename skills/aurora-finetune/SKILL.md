---
name: aurora-finetune
description: Train, resume, warm-start, or replay one of Aurora's versioned residual-refinement heads using the existing frozen-baseline backend. Use when changing a refinement experiment or checkpoint.
---

# Train or replay a refinement head

Read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md), [model contracts](../../knowledge/models/refinement.md), and [runbook](../../docs/claude-code-plugin.md).

1. Inspect with `inspect_environment`, `inspect_assets`, and `list_runs`; call `validate_recipe` for `no2-us-west-v1` or `o3-global-v1`.
2. Select exactly one head: `flow_matching_conv_unet`, `flow_matching_transformer`, `diffusion_unet`, or `diffusion_transformer`. `flow_matching_unet` is a separate historical adapter, not an alias for `flow_matching_conv_unet`. Preserve recipe defaults, `AuroraAirPollution`, a frozen baseline, `feedback_to_rollout=false`, and the spatial-only portable recipe.
3. Choose the actual mode. `replay` requires a compatible trained checkpoint and never trains; `resume` requires recoverable optimizer/scheduler/RNG state; `warm-start` begins a named new optimizer experiment from compatible weights; `reproduce` trains a new experiment; `evaluate` does not train. If required checkpoint metadata/artifacts are missing, report `requires_artifact`, do not substitute fresh training.
4. Call `plan_execution` with the recipe, exact head, mode, case ID, existing artifact paths, point/ensemble choice, seed and explicit resource bounds. Review missing inputs, effective config hash, stages, storage, GPU and time limits with the operator.
5. Do not call execution tools until the operator approves the plan in their own terminal. Then use `execute_workflow` once; track its durable job with `job_status` and bounded `job_logs`. Use `recover_job` only for the unchanged approved job.
6. The backend preserves separate deterministic point and stochastic ensemble products, raw baseline fields, checkpoint compatibility, and provenance. Report the produced checkpoint, manifest, product identity and actual optimizer progress; synthetic smoke execution is not real-data evidence.
