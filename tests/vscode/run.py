#!/usr/bin/env python3
"""Opt-in real VS Code extension-host smoke test; needs a display (Xvfb works).

No model/account session or scientific computation is started. The test installs
the local Aurora plugin in a disposable home and permits minimal pip bootstrap.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", required=True, help="Absolute VS Code desktop executable (not the remote CLI)")
    parser.add_argument("--claude-extension", required=True, help="Installed Claude Code extension directory")
    parser.add_argument("--root", help="New disposable output directory")
    parser.add_argument("--display", default=os.environ.get("DISPLAY", ":0"))
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else Path(tempfile.mkdtemp(prefix="aurora-vscode-"))
    if args.root:
        root.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[2]
    workspace = root / "workspace"
    workspace.mkdir()
    files = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=repo).split(b"\0")
    for item in files:
        if not item:
            continue
        relative = Path(os.fsdecode(item))
        source = repo / relative
        if not source.exists() and not source.is_symlink():
            continue
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)
    (workspace / ".vscode").mkdir()
    shutil.copy2(repo / "docs/clients/vscode-mcp.example.json", workspace / ".vscode/mcp.json")
    home = root / "home"
    home.mkdir()
    extensions = root / "extensions"
    extensions.mkdir()
    claude_extension = Path(args.claude_extension).resolve()
    (extensions / claude_extension.name).symlink_to(claude_extension, target_is_directory=True)
    user_data = root / "user-data"
    (user_data / "User").mkdir(parents=True)
    (user_data / "User/settings.json").write_text(json.dumps({
        "telemetry.telemetryLevel": "off", "update.mode": "none",
        "extensions.autoUpdate": False, "extensions.autoCheckUpdates": False,
        "chat.mcp.autostart": "never", "security.workspace.trust.enabled": False,
    }))
    environment = {k: v for k, v in os.environ.items()
                   if not k.startswith(("AURORA_", "VSCODE_", "CDSAPI_", "XDG_", "ELECTRON_", "PYTHON"))
                   and not any(word in k.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))}
    environment.update(HOME=str(home), DISPLAY=args.display, DISABLE_AUTOUPDATER="1",
                       AURORA_VSCODE_TEST_REPORT=str(root / "report.json"))
    binary = claude_extension / "resources/native-binary/claude"
    for command in (["plugin", "marketplace", "add", str(workspace)],
                    ["plugin", "install", "aurora-air-pollution@aurora"]):
        subprocess.run([str(binary), *command], env=environment, cwd=root, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
    command = [str(Path(args.code).resolve()), "--no-sandbox", "--disable-gpu", "--password-store=basic",
               "--skip-welcome", "--skip-release-notes", "--disable-workspace-trust",
               f"--user-data-dir={user_data}", f"--extensions-dir={extensions}",
               f"--extensionDevelopmentPath={workspace / 'tests/vscode'}",
               f"--extensionTestsPath={workspace / 'tests/vscode/test.cjs'}",
               "--enable-proposed-api", "midatm1234.aurora-onboarding-test", str(workspace)]
    with (root / "vscode.log").open("w") as log:
        result = subprocess.run(command, env=environment, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=360)
    report_path = root / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    print(json.dumps({"exit_code": result.returncode, "passed": report.get("passed", False),
                      "vscode": report.get("vscode"), "report": str(report_path), "log": str(root / "vscode.log"),
                      "checks": [row["name"] for row in report.get("checks", [])]}, indent=2))
    raise SystemExit(result.returncode or (0 if report.get("passed") else 1))


if __name__ == "__main__":
    main()
