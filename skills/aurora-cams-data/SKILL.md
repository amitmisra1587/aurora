---
name: aurora-cams-data
description: Plan, retrieve and validate recipe-matched CAMS operational inputs for AuroraAirPollution. Use when CAMS data are missing or need verification; do not substitute analyses, forecasts or reanalysis silently.
---

# Acquire and prepare CAMS inputs

Read the packaged [canonical workflow](../../.agents/skills/msresearch-aurora-air-pollution/SKILL.md), [CAMS contract](../../knowledge/data/cams.md), [leakage contract](../../knowledge/data/leakage.md), and [runbook](../../docs/claude-code-plugin.md).

1. Call `inspect_environment`, `inspect_assets`, and `list_runs`; reuse only compatible, checksum-verified local data.
2. Call `validate_recipe` for `no2-us-west-v1` or `o3-global-v1`. Read the recipe's selected target variables, levels, domain and operational reference kind; never replace its full-backbone inputs with target-only acquisitions.
3. Call `plan_execution` with the selected recipe, mode `reproduce`, a unique `case_id`, an explicit `data` override for UTC initialization `cycles` or `start_date`/`end_date`, `lead_hours`, `target_variables`, `target_levels`, and `domain` only where needed, and strict `max_requests`, `max_download_bytes`, `max_disk_bytes`, and `max_wall_seconds`. Use `stages: ["sources", "acquire"]` for an acquisition-only plan, or include `prepare` to validate/prepare the acquired inputs. Keep backbone variables, pressure levels, cadence, history and global acquisition as specified by the recipe/backend.
4. Present the exact returned request count, estimated bytes, source product/reference kind, date coverage (including the preceding history), stages, output roots and unknown costs. Do not call `acquire_cams` until the operator has approved this exact plan in their interactive terminal.
5. After approval, call `acquire_cams` once with the returned `plan_id`; monitor its durable job using `job_status` and bounded `job_logs`. Use `recover_job` only for an interrupted job under unchanged approval, and `cancel_job` when requested. For preparation, execute the already-planned `prepare_dataset` stage; do not silently re-plan or resubmit a completed chunk.
6. Report chunk receipts, output paths, checksums, initialization/lead/valid-time coverage, validation failures and provenance. The backend refuses incomplete/history-invalid data rather than returning success-shaped output.

For a short, bounded regional example, start with a small recipe-covered interval and request limits before adding historical dates. The server uses official CAMS ADS request forms and its pinned `cdsapi` client; ADS credentials are configured locally and dataset terms are accepted manually. An operational CAMS product is a model reference, not independent observational truth.
