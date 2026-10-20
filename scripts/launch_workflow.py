#!/usr/bin/env python3
"""Dependency-free first-run supervisor; all workflow tools run in the official MCP SDK.

The small stdio bridge answers initialization/status during pip installation, then
forwards requests unchanged to the shared backend. No scientific executor lives here.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "2025-11-25"
VERSION = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())["version"]
SETUP_TOOLS = [
    {"name": "setup_status", "description": "Inspect lightweight setup progress, paths and recovery instructions; no science runs.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "setup_retry", "description": "Retry failed lightweight setup after fixing local settings or network access; never installs science packages.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def absolute(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Launcher path values must be nonempty strings.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("Launcher paths must be absolute (or start with ~).")
    return path.resolve()


class Setup:
    def __init__(self):
        self.state = "starting"
        self.message = "Preparing the minimal MCP environment; scientific packages are deferred."
        self.paths = {}
        self.child = None
        self.installer = None
        self.cancelled = False
        self.environment = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}

    def status(self):
        return {"state": self.state, "message": self.message, **self.paths,
                "plugin_root": str(ROOT), "launcher": str(ROOT / "bin/aurora-mcp"),
                "next_step": "Call inspect_environment, inspect_assets and list_runs." if self.state == "ready" else
                "Poll setup_status. After correcting a failure, call setup_retry or reconnect. If tools do not refresh, restart the MCP server."}

    def stop_install(self):
        self.cancelled = True
        if self.installer:
            try:
                os.killpg(self.installer.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def prepare(self):
        config_home = absolute(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "aurora"
        settings_file = config_home / "launcher.json"
        self.paths = {"settings": str(settings_file)}
        try:
            options = json.loads(settings_file.read_text()) if settings_file.exists() else {}
        except (OSError, ValueError) as exc:
            raise ValueError(f"Cannot read launcher settings at {settings_file}; correct JSON and file permissions, then retry.") from exc
        if not isinstance(options, dict) or set(options) - {"workspace", "venv", "config"}:
            raise ValueError(f"Expected only workspace, venv and config paths in {settings_file}")
        cache = absolute(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "aurora-air-pollution"
        lock_hash = hashlib.sha256((ROOT / "requirements/workflow-light.txt").read_bytes()).hexdigest()[:12]
        default_venv = cache / f"venv-{sys.version_info.major}.{sys.version_info.minor}-{lock_hash}"
        workspace = absolute(os.environ.get("AURORA_WORKSPACE", options.get("workspace", str(Path.home() / "aurora-air-pollution-work"))))
        config = absolute(os.environ.get("AURORA_WORKFLOW_CONFIG", options.get("config", str(config_home / "workflow.json"))))
        venv = absolute(os.environ.get("AURORA_WORKFLOW_VENV", options.get("venv", str(default_venv))))
        self.paths = {"settings": str(settings_file), "config": str(config), "workspace": str(workspace), "venv": str(venv)}
        for path in (config, workspace, venv):
            if path.is_relative_to(ROOT):
                raise ValueError("Keep configuration, environments and workspace outside the installed plugin; edit launcher.json.")
        # Reuse the previous launcher's environment only when the minimal pins match.
        if venv == default_venv and self.compatible(cache / "venv"):
            venv = cache / "venv"
            self.paths["venv"] = str(venv)
        log = venv.parent / (venv.name + ".setup.log")
        self.paths["log"] = str(log)
        venv.parent.mkdir(parents=True, exist_ok=True)
        # flock releases on process death; concurrent client launches share one install.
        with (venv.parent / (venv.name + ".setup.lock")).open("a") as lock:
            self.state = "waiting_for_setup"
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.cancelled:
                return
            if not self.compatible(venv):
                self.state = "installing"
                self.message = "Installing pinned MCP/metadata packages only; progress is in the private setup log."
                print(f"[aurora-mcp] {self.message} {log}", file=sys.stderr)
                with os.fdopen(os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a") as output:
                    self.installer = subprocess.Popen([sys.executable, str(ROOT / "scripts/bootstrap_workflow.py"),
                                                       "--venv", str(venv), "--no-project"],
                                                      cwd=ROOT, env=self.environment, stdout=output, stderr=output,
                                                      start_new_session=True)
                    if self.cancelled:
                        self.stop_install()
                    returncode = self.installer.wait()
                    self.installer = None
                if returncode or not self.compatible(venv):
                    raise RuntimeError("Minimal dependency installation failed. Check the setup log for pip/venv/network errors. "
                                       "Install Python's venv/pip support or restore package-index access, then retry. "
                                       "An incompatible existing environment is preserved: choose a new venv path in launcher.json.")
        if self.cancelled:
            return
        self.python = str(venv / "bin/python")
        self.state = "configuring"
        # Serialize creation separately: different environments can share one config.
        config.parent.mkdir(parents=True, exist_ok=True)
        with config.with_name(config.name + ".setup.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not config.exists():
                result = subprocess.run([self.python, "-m", "aurora_workflow", "--config", str(config),
                                         "configure", "--workspace", str(workspace)],
                                        cwd=ROOT, env=self.environment, capture_output=True)
                if result.returncode:
                    raise ValueError(f"Cannot create dedicated workspace configuration at {config}; check path permissions and launcher.json.")
            valid = subprocess.run([self.python, "-c",
                                    "import sys; from aurora_workflow.settings import Settings; Settings.load(sys.argv[1])", str(config)],
                                   cwd=ROOT, env=self.environment, capture_output=True)
            if valid.returncode:
                raise ValueError(f"Invalid workflow configuration at {config}. Use valid JSON with data_root, cache_root, output_root and state_root. "
                                 "Use absolute dedicated roots, keep state outside read/data/cache/output roots, "
                                 "and remove unsupported keys. Existing configuration was preserved.")
        self.state = "prepared"
        self.message = "Minimal setup ready. No datasets, credentials, weights, PyTorch or GPU were required."
        self.paths["approval_command"] = [str(ROOT / "bin/aurora-mcp"), "--approve", "PLAN_ID"]

    @staticmethod
    def compatible(venv):
        python = venv / "bin/python"
        if not python.is_file():
            return False
        pins = [line.strip().split("==") for line in (ROOT / "requirements/workflow-light.txt").read_text().splitlines()
                if "==" in line and not line.lstrip().startswith("#")]
        try:
            return subprocess.run([str(python), "-c",
                                   "import sys, json, importlib.metadata as m; import mcp, pydantic, yaml; "
                                   "assert (3,12) <= sys.version_info[:2] <= (3,14); "
                                   "assert all(m.version(k)==v for k,v in json.loads(sys.argv[1]))", json.dumps(pins)],
                                  capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


class Bridge:
    def __init__(self, setup):
        self.setup = setup
        self.output_lock = threading.Lock()
        self.child_lock = threading.Lock()
        self.initialized = False
        self.pending = {}
        self.start_lock = threading.Lock()
        self.thread = None
        self.closed = False

    def send(self, message):
        if self.closed:
            return
        with self.output_lock:
            sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    def result(self, request, result):
        self.send({"jsonrpc": "2.0", "id": request["id"], "result": result})

    def changed(self):
        if self.initialized:
            self.send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})

    def start(self):
        with self.start_lock:
            if self.thread and self.thread.is_alive():
                return
            self.setup.state = "starting"
            self.setup.cancelled = False
            self.thread = threading.Thread(target=self.prepare_backend, daemon=True)
            self.thread.start()

    def prepare_backend(self):
        child = None
        try:
            self.setup.prepare()
            self.setup.state = "connecting"
            if self.closed:
                return
            child = subprocess.Popen([self.setup.python, "-m", "aurora_workflow.mcp_server", "--config", self.setup.paths["config"]],
                                     cwd=ROOT, env=self.setup.environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, bufsize=1)
            child.stdin.write(json.dumps({"jsonrpc": "2.0", "id": "aurora-bootstrap", "method": "initialize", "params": {
                "protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "aurora-launcher", "version": VERSION}}}) + "\n")
            child.stdin.flush()
            hello = json.loads(child.stdout.readline())
            if "result" not in hello:
                raise RuntimeError("Backend initialization failed; reconnect and inspect client stderr.")
            child.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            child.stdin.flush()
            with self.child_lock:
                if self.closed:
                    return
                self.setup.child = child
                self.setup.state = "ready"
            self.changed()
            for line in child.stdout:
                message = json.loads(line)
                request = self.pending.pop(message.get("id"), None)
                if request and request.get("method") == "tools/list" and "result" in message:
                    message["result"]["tools"] = SETUP_TOOLS + message["result"].get("tools", [])
                self.send(message)
            raise RuntimeError("MCP backend stopped. Reconnect, or call setup_retry; scientific jobs remain in the workspace.")
        except Exception as exc:
            if self.closed:
                return
            self.setup.state = "failed"
            self.setup.message = str(exc)
            print(f"[aurora-mcp] {exc}", file=sys.stderr)
            for request in list(self.pending.values()):
                self.send({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32603, "message": "Backend stopped; call setup_status."}})
            self.pending.clear()
        finally:
            with self.child_lock:
                self.setup.child = None
            if child and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()

    def handle(self, request):
        method = request.get("method")
        if method == "initialize":
            requested = request.get("params", {}).get("protocolVersion")
            protocol = requested if requested in {"2024-11-05", "2025-03-26", "2025-06-18", PROTOCOL} else PROTOCOL
            self.result(request, {"protocolVersion": protocol, "capabilities": {"tools": {"listChanged": True}, "resources": {}},
                                  "serverInfo": {"name": "Aurora air-pollution workflow", "version": VERSION},
                                  "instructions": "Call setup_status during first-run installation. Once ready, inspect_environment, inspect_assets and list_runs. "
                                  "Read aurora://instructions and knowledge_read(index.md). Scientific execution requires a bounded plan and human terminal approval."})
        elif method == "notifications/initialized":
            self.initialized = True
            self.changed()
        elif method == "ping":
            self.result(request, {})
        elif method == "tools/call" and request.get("params", {}).get("name") in {"setup_status", "setup_retry"}:
            if request["params"]["name"] == "setup_retry" and self.setup.state == "failed":
                self.start()
            status = self.setup.status()
            self.result(request, {"content": [{"type": "text", "text": json.dumps(status)}], "structuredContent": status, "isError": False})
        elif self.setup.state == "ready" and self.setup.child:
            with self.child_lock:
                if "id" in request:
                    self.pending[request["id"]] = request
                self.setup.child.stdin.write(json.dumps(request) + "\n")
                self.setup.child.stdin.flush()
        elif method == "tools/list":
            self.result(request, {"tools": SETUP_TOOLS})
        elif method in {"resources/list", "resources/templates/list", "prompts/list"}:
            key = {"resources/list": "resources", "resources/templates/list": "resourceTemplates", "prompts/list": "prompts"}[method]
            self.result(request, {key: []})
        elif "id" in request:
            self.send({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32000, "message": "Workflow tools are preparing. Call setup_status for progress/recovery."}})

    def run(self):
        self.start()
        try:
            for line in sys.stdin:
                self.handle(json.loads(line))
        finally:
            with self.child_lock:
                self.closed = True
                if self.setup.child:
                    self.setup.child.terminate()
                self.setup.stop_install()
            if self.thread:
                self.thread.join(timeout=6)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "serve"
    setup = Setup()
    if action in {"serve", "--config"}:
        Bridge(setup).run()
        return
    try:
        try:
            setup.prepare()
        except Exception as exc:
            print(f"[aurora-mcp] {exc}", file=sys.stderr)
            raise SystemExit(2)
    finally:
        setup.stop_install()
    setup.state = "ready"
    if action == "--install":
        print(json.dumps(setup.status(), indent=2))
        return
    command = [setup.python, "-m", "aurora_workflow", "--config", setup.paths["config"]]
    command += ["approve", os.environ["AURORA_APPROVE_PLAN"]] if action == "--approve" else ["doctor"]
    os.execve(setup.python, command, setup.environment)


if __name__ == "__main__":
    def terminate(_signum, _frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, terminate)
    main()
