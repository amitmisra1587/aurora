"""Static Claude plugin/package checks; no Claude client, network, or scientific assets required."""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

import pytest
import yaml

from aurora_workflow import common

ROOT = Path(__file__).resolve().parents[2]
TOOL_PREFIX = re.compile(
    r"\b(?:inspect|list|validate|plan|execute|prepare|retrieve|acquire|run|train|evaluate|generate|"
    r"job|cancel|recover|knowledge)_[a-z][a-z0-9_]*\b"
)
NON_TOOL_IDENTIFIERS = {"plan_id", "job_id"}


def _declared_tools() -> set[str]:
    tree = ast.parse((ROOT / "aurora_workflow/mcp_server.py").read_text())
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(decorator, ast.Name) and decorator.id == "tool"
                for decorator in node.decorator_list)
    }


def _check_installed_skill_links(root):
    """References must remain inside a copied plugin, without the source checkout."""
    for skill in [*root.glob("skills/*/SKILL.md"),
                  root / ".agents/skills/msresearch-aurora-air-pollution/SKILL.md"]:
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", skill.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (skill.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(root.resolve()), (skill, target)
            assert resolved.is_file(), (skill, target)


def test_manifests_and_plugin_mcp_registration_are_consistent():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    mcp = plugin
    entry = marketplace["plugins"][0]

    assert plugin["name"] == "aurora-air-pollution"
    assert marketplace["name"] == "aurora"
    assert entry["name"] == plugin["name"]
    assert entry["source"] == "./"
    assert plugin["skills"] == ["./skills/"]
    assert list(mcp["mcpServers"]) == ["aurora-air-pollution"]
    server = mcp["mcpServers"]["aurora-air-pollution"]
    assert server == {"command": "${CLAUDE_PLUGIN_ROOT}/bin/aurora-mcp", "args": []}
    assert not (ROOT / ".mcp.json").exists()  # No duplicate project-scope server.
    assert stat.S_IMODE((ROOT / "bin/aurora-mcp").stat().st_mode) & stat.S_IXUSR


def test_docker_targets_are_pinned_non_root_and_exclude_private_artifacts():
    dockerfile = (ROOT / "Dockerfile.workflow").read_text()
    ignored = (ROOT / ".dockerignore").read_text()
    assert "python:3.12.11-slim-bookworm" in dockerfile
    assert "nvcr.io/nvidia/pytorch:25.08-py3" in dockerfile
    assert "FROM ${PYTHON_IMAGE} AS cpu" in dockerfile
    assert "FROM nvcr.io/nvidia/pytorch:25.08-py3 AS cuda" in dockerfile
    assert dockerfile.count("USER aurora") == 2
    assert "ENTRYPOINT [\"/opt/aurora/bin/aurora-mcp\"]" in dockerfile
    assert ".cdsapirc" in ignored and "*.ckpt" in ignored and "data/" in ignored
    assert "docker.sock" not in dockerfile and "privileged" not in dockerfile


def test_skill_frontmatter_links_and_tool_names_are_packaged():
    actual_tools = _declared_tools()
    skill_dirs = sorted((ROOT / "skills").glob("*/"))
    assert {p.name for p in skill_dirs} == {
        "aurora-setup", "aurora-cams-data", "aurora-finetune", "aurora-evaluate", "aurora-reproduce"
    }
    discovered_names = set()
    for directory in skill_dirs:
        skill = directory / "SKILL.md"
        text = skill.read_text()
        assert text.startswith("---\n")
        _, frontmatter, body = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert metadata["name"] == directory.name
        assert isinstance(metadata["description"], str) and metadata["description"].strip()
        assert metadata["name"] not in discovered_names
        discovered_names.add(metadata["name"])
        for tool_name in TOOL_PREFIX.findall(body):
            if tool_name in NON_TOOL_IDENTIFIERS:
                continue
            assert tool_name in actual_tools, f"{skill}: unknown MCP tool {tool_name}"
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
            if target.startswith(("https://", "http://", "#")):
                continue
            relative = target.split("#", 1)[0]
            assert (directory / relative).resolve().is_file(), f"{skill}: broken link {target}"

    for packaged in (
        ".agents/skills/msresearch-aurora-air-pollution/SKILL.md",
        ".agents/skills/msresearch-aurora-air-pollution/references/workflow.md",
        ".agents/skills/msresearch-aurora-air-pollution/references/evidence.md",
        "knowledge/index.md",
        "recipes/no2-us-west-v1.json",
        "recipes/o3-global-v1.json",
        "aurora_workflow/mcp_server.py",
    ):
        assert (ROOT / packaged).is_file()
    assert "msresearch-aurora-air-pollution" not in discovered_names


def test_source_fingerprint_remains_available_without_git_metadata(monkeypatch):
    def unavailable(*_args: str) -> str:
        raise subprocess.CalledProcessError(128, ["git"])

    monkeypatch.setattr(common, "git", unavailable)
    record = common.source_fingerprint()
    assert record["commit"] is None
    assert record["dirty"] is None
    assert len(record["code_hash"]) == 64
    assert record["imported_workflow_path"] == str(ROOT)


def test_launcher_actionable_missing_python_from_outside_checkout(tmp_path):
    fake_path = tmp_path / "bin"
    fake_path.mkdir()
    (fake_path / "dirname").symlink_to(shutil.which("dirname"))
    env = {**os.environ, "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config"),
           "XDG_CACHE_HOME": str(tmp_path / "cache"), "PATH": str(fake_path),
           "AURORA_PYTHON": "", "AURORA_WORKFLOW_VENV": str(tmp_path / "missing-venv")}
    result = subprocess.run([str(ROOT / "bin/aurora-mcp")], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "Python 3.12" in result.stderr and "client's PATH" in result.stderr
    assert result.stdout == ""


def test_launcher_check_runs_doctor_without_starting_mcp(tmp_path):
    config = tmp_path / "workflow.json"
    config.write_text(json.dumps({
        "data_root": str(tmp_path / "data"),
        "cache_root": str(tmp_path / "cache"),
        "output_root": str(tmp_path / "runs"),
        "state_root": str(tmp_path / "state"),
    }))
    python_root = Path(os.sys.executable).absolute().parent.parent
    result = subprocess.run(
        [str(ROOT / "bin/aurora-mcp"), "--check"],
        cwd=tmp_path,
        env={**os.environ, "AURORA_WORKFLOW_CONFIG": str(config),
             "AURORA_WORKFLOW_VENV": str(python_root), "PYTHONPATH": str(ROOT)},
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["fork_import_verified"]
    assert set(report["credentials_present"]) == {"ads_local_config", "ads_environment"}
    assert result.stderr == ""


def test_docker_launcher_preserves_paths_and_read_only_credentials(tmp_path):
    fake_bin = tmp_path / "fake bin"
    fake_bin.mkdir()
    docker = fake_bin / "docker"
    docker.write_text("#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n")
    docker.chmod(0o755)
    workspace = tmp_path / "workspace with spaces"
    config_dir = tmp_path / "config with spaces"
    workspace.mkdir()
    config_dir.mkdir()
    config = config_dir / "workflow.json"
    config.write_text("{}")
    ads_config = tmp_path / "ADS credentials"
    ads_config.write_text("url: https://example.invalid\nkey: redacted\n")
    env = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "AURORA_WORKFLOW_DOCKER_IMAGE": "aurora-workflow:test",
        "AURORA_WORKSPACE": str(workspace),
        "AURORA_WORKFLOW_DOCKER_CONFIG": str(config),
        "CDSAPI_RC": str(ads_config),
    }
    result = subprocess.run(
        [str(ROOT / "bin/aurora-mcp"), "--check"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert f"type=bind,src={workspace},dst=/workspace" in args
    assert f"type=bind,src={config},dst=/config/workflow.json,readonly" in args
    assert f"type=bind,src={ads_config},dst=/config/ads.credentials,readonly" in args
    assert args[-2:] == ["aurora-workflow:test", "--check"]


def test_plugin_launcher_starts_stdio_server_outside_checkout(tmp_path):
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import asyncio

    installed_root = tmp_path / "installed-plugin"
    copy_items = (
        ".agents", ".claude-plugin", "aurora", "aurora_workflow",
        "bin", "docs", "finetune", "knowledge", "provenance", "recipes",
        "requirements", "skills", "scripts",
    )
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.ipynb", "*.ckpt",
                                   "*.pt", "*.pth", "*.pickle", "*.npz", "*.nc")
    installed_root.mkdir()
    for name in copy_items:
        source = ROOT / name
        destination = installed_root / name
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore)
        else:
            shutil.copy2(source, destination)
    _check_installed_skill_links(installed_root)

    config = tmp_path / "workflow.json"
    config.write_text(json.dumps({
        "data_root": str(tmp_path / "data"),
        "cache_root": str(tmp_path / "cache"),
        "output_root": str(tmp_path / "runs"),
        "state_root": str(tmp_path / "state"),
    }))
    python_root = Path(os.sys.executable).absolute().parent.parent

    async def check():
        params = StdioServerParameters(
            command=str(installed_root / "bin/aurora-mcp"),
            args=[],
            cwd=str(tmp_path),
            env={**os.environ, "AURORA_WORKFLOW_CONFIG": str(config),
                 "AURORA_WORKFLOW_VENV": str(python_root), "PYTHONPATH": str(installed_root)},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                for _ in range(300):
                    status = (await client.call_tool("setup_status", {})).structuredContent
                    assert status["state"] != "failed", status
                    if status["state"] == "ready":
                        break
                    await asyncio.sleep(.1)
                assert status["state"] == "ready", status
                tools = await client.list_tools()
                assert "inspect_environment" in {tool.name for tool in tools.tools}
                assert {"setup_status", "setup_retry"} <= {tool.name for tool in tools.tools}
                resources = await client.list_resources()
                assert "aurora://instructions" in {str(r.uri) for r in resources.resources}
                instructions = await client.read_resource("aurora://instructions")
                assert "feedback_to_rollout=false" in instructions.contents[0].text
                assert (await client.read_resource("aurora://workflow-routing")).contents[0].text
                assert (await client.read_resource("aurora://evidence")).contents[0].text
                environment = await client.call_tool("inspect_environment", {})
                assert environment.structuredContent["fork_import_verified"]
                result = await client.call_tool("list_runs", {})
                assert result.structuredContent["jobs"] == []
                recipe = await client.call_tool("validate_recipe", {"recipe": "cpu-smoke-v1", "head": "none"})
                assert recipe.structuredContent["state"] == "validated"
                plan = await client.call_tool(
                    "plan_execution",
                    {"request": {"recipe": "cpu-smoke-v1", "head": "none", "case_id": "cache-plan"}},
                )
                assert plan.structuredContent["source"]["commit"] is None
                assert len(plan.structuredContent["source"]["code_hash"]) == 64

    asyncio.run(check())


def test_failed_first_setup_stays_connected_and_can_retry_configuration(tmp_path):
    """No package installs: compatible existing environment, initially invalid JSON."""
    import asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    config_home = tmp_path / "config"
    (config_home / "aurora").mkdir(parents=True)
    options = config_home / "aurora/launcher.json"
    options.write_text("{")
    env = {**os.environ, "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(config_home),
           "XDG_CACHE_HOME": str(tmp_path / "cache"),
           "AURORA_WORKFLOW_VENV": str(Path(os.sys.executable).absolute().parent.parent)}
    env.pop("AURORA_WORKFLOW_CONFIG", None)

    async def poll(client, expected):
        for _ in range(200):
            status = (await client.call_tool("setup_status", {})).structuredContent
            if status["state"] == expected:
                return status
            await asyncio.sleep(.05)
        pytest.fail(str(status))

    async def exercise():
        async with stdio_client(StdioServerParameters(command=str(ROOT / "bin/aurora-mcp"), cwd=str(tmp_path), env=env)) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                await poll(client, "failed")
                assert {t.name for t in (await client.list_tools()).tools} == {"setup_status", "setup_retry"}
                options.write_text(json.dumps({"workspace": str(tmp_path / "chosen workspace")}))
                await client.call_tool("setup_retry", {})
                status = await poll(client, "ready")
                inspected = (await client.call_tool("inspect_environment", {})).structuredContent
                assert inspected["roots"]["data_root"]["path"] == str(tmp_path / "chosen workspace/data")
                assert json.loads(Path(status["config"]).read_text())["assets"] == {}
                assert (await client.call_tool("knowledge_validate", {})).structuredContent["ok"]
    asyncio.run(exercise())


def test_setup_preserves_invalid_existing_workflow_config(tmp_path):
    config = tmp_path / "invalid.json"
    original = '{"data_root":"relative"}'
    config.write_text(original)
    env = {**os.environ, "AURORA_WORKFLOW_CONFIG": str(config),
           "AURORA_WORKFLOW_VENV": str(Path(os.sys.executable).absolute().parent.parent)}
    result = subprocess.run([str(ROOT / "bin/aurora-mcp"), "--check"], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2 and "Invalid workflow configuration" in result.stderr
    assert result.stdout == "" and config.read_text() == original
