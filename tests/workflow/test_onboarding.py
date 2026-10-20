"""Onboarding failure recovery offline; optional real pip install into a fresh home."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest

from aurora_workflow.common import REPO


def clean_environment(root):
    # Do not inherit the developer's Aurora paths, credentials or Python imports.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("AURORA_", "CDSAPI_", "PYTHON", "XDG_"))
           and not any(word in k.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))}
    env.update(HOME=str(root), XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"), AURORA_PYTHON=sys.executable,
               PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES="")
    return env


async def wait_for_setup(client, terminal, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        status = (await client.call_tool("setup_status", {})).structuredContent
        if status["state"] in terminal:
            return status
        await asyncio.sleep(.1)
    pytest.fail(f"Setup did not reach {terminal}: {status}")


def test_failed_dependency_install_connects_immediately_and_preserves_retry_state(tmp_path):
    env = clean_environment(tmp_path)
    env["PIP_NO_INDEX"] = "1"  # deterministic pip failure, no network access

    async def exercise():
        params = StdioServerParameters(command=str(REPO / "bin/aurora-mcp"), cwd=str(tmp_path), env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                start = time.monotonic()
                await client.initialize()
                assert time.monotonic() - start < 5
                assert "setup_status" in {t.name for t in (await client.list_tools()).tools}
                failed = await wait_for_setup(client, {"failed"})
                assert "installation failed" in failed["message"]
                marker = Path(failed["venv"]) / ".aurora-workflow-environment.json"
                assert json.loads(marker.read_text())["state"] == "installing"
                assert Path(failed["log"]).is_file()
                assert Path(failed["log"]).stat().st_mode & 0o777 == 0o600
                await client.call_tool("setup_retry", {})
                repeated = await wait_for_setup(client, {"failed"})
                assert repeated["venv"] == failed["venv"]
                assert "installation failed" in repeated["message"]
                assert not Path(failed["config"]).exists()
    asyncio.run(exercise())


@pytest.mark.skipif(os.environ.get("AURORA_TEST_FRESH_INSTALL") != "1",
                    reason="Opt-in network test: AURORA_TEST_FRESH_INSTALL=1 installs light pins into a temporary home")
def test_clean_install_restart_and_external_configuration(tmp_path):
    launcher = Path(os.environ.get("AURORA_TEST_LAUNCHER", str(REPO / "bin/aurora-mcp"))).resolve()
    env = clean_environment(tmp_path)
    from .test_claude_plugin import _check_installed_skill_links
    _check_installed_skill_links(launcher.parents[1])

    async def connect():
        params = StdioServerParameters(command=str(launcher), cwd=str(tmp_path), env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                start = time.monotonic()
                result = await client.initialize()
                assert time.monotonic() - start < 5
                assert result.protocolVersion == "2025-11-25"
                status = await wait_for_setup(client, {"ready", "failed"}, seconds=240)
                assert status["state"] == "ready", status
                tools = {t.name for t in (await client.list_tools()).tools}
                assert len(tools) == 26
                assert {"setup_status", "inspect_environment", "knowledge_read"} <= tools
                inspected = (await client.call_tool("inspect_environment", {})).structuredContent
                assert inspected["fork_import_verified"]
                assert not any(inspected["credentials_present"].values())
                assert inspected["dependencies"]["torch"] is None
                assert inspected["dependencies"]["numpy"] is None
                assert (await client.call_tool("list_runs", {})).structuredContent["jobs"] == []
                assert (await client.call_tool("knowledge_validate", {})).structuredContent["ok"]
                resources = {str(r.uri) for r in (await client.list_resources()).resources}
                assert resources == {"aurora://instructions", "aurora://workflow-routing", "aurora://evidence"}
                for resource in resources:
                    assert (await client.read_resource(resource)).contents[0].text
                assert (await client.call_tool("knowledge_read", {"concept": "index.md"})).structuredContent["ok"]
                return status

    first = asyncio.run(connect())
    config = Path(first["config"])
    original = config.read_bytes()
    # Reconnect and rerun explicit setup; neither may reset custom configuration.
    second = asyncio.run(connect())
    assert second["venv"] == first["venv"]
    checked = subprocess.run([str(launcher), "--check"], cwd=tmp_path, env=env,
                             capture_output=True, text=True, timeout=30)
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["fork_import_verified"]
    assert config.read_bytes() == original
