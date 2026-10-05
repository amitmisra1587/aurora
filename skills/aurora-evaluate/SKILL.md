---
name: aurora-evaluate
description: Evaluate matched Aurora baseline and refined forecasts against the same CAMS reference in physical units, with coverage and provenance. Use for report generation or head comparisons.
---

# Evaluate forecasts

Read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md), [evaluation contract](../../knowledge/evaluation/metrics.md), [physical-unit contract](../../knowledge/data/physical-units.md), and [runbook](../../docs/claude-code-plugin.md).

1. Call `inspect_environment`, `inspect_assets`, and `list_runs`. Locate compatible baseline, refined point or ensemble product, same-CAMS-reference artifacts and their manifests/checksums. Do not infer that products are matched from filenames.
2. For existing outputs, call `plan_execution` with `mode: "evaluate"`, explicit `inputs` for the matched artifacts, the selected versioned recipe and `evaluation` options. For an integrated new run, use `aurora-reproduce` instead.
3. Show the exact plan, sample/coverage limits, resource bounds and output location. Evaluation is local computation; still use the backend's approval boundary for any plan stage that requires authorization. Never pass or fabricate approval.
4. Execute through `evaluate_forecasts`/`generate_report` under the approved plan, then inspect `job_status` and `job_logs`. Report `metrics.json`, `metrics.svg`, `evaluation.md`, manifest and receipts from the successful run.
5. Compare identical cases, coordinates, masks and physical units. Preserve negative changes and coverage/exclusions. Keep deterministic point and stochastic ensemble scores separate. CAMS model-reference agreement is not independent observational validation.

To compare all four unified heads, require a compatible checkpoint/output for each and evaluate each against the same baseline and reference; do not train missing heads as a side effect or imply that four fixture smoke runs measure forecast skill.
