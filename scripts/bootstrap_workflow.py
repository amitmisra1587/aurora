#!/usr/bin/env python3
"""Explicit, repeatable operator-run bootstrap; never downloads scientific assets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import venv


def lock_digest(repo: Path, mode: str) -> str:
    files = {
        "light": ("workflow-light.txt",),
        "data": ("workflow-light.txt", "workflow-data.txt"),
        "science": ("workflow-light.txt", "workflow-data.txt", "workflow-cpu.txt"),
    }[mode]
    content = b"".join(
        name.encode() + b"\0" + (repo / "requirements" / name).read_bytes() + b"\0"
        for name in files
    )
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv", required=True)
    parser.add_argument("--no-project", action="store_true",
                        help="Use the launcher's PYTHONPATH instead of an editable install (plugin caches)")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--data", action="store_true",
                       help="Install pinned CAMS acquisition/preparation dependencies without PyTorch")
    modes.add_argument("--science", action="store_true",
                       help="Install CPU PyTorch and the complete scientific dependency set")
    args = parser.parse_args()
    if not (3, 12) <= sys.version_info[:2] <= (3, 14):
        raise SystemExit("Use Python 3.12–3.14; CI uses 3.12 and local validation records exact interpreter.")
    target = Path(args.venv).expanduser().resolve()
    repo = Path(__file__).resolve().parents[1]
    mode = "science" if args.science else "data" if args.data else "light"
    marker = target / ".aurora-workflow-environment.json"
    python_path = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    expected = {"mode": mode, "requirements_sha256": lock_digest(repo, mode)}
    if target.exists():
        if not marker.is_file() or not python_path.is_file():
            try:
                existing = json.loads(marker.read_text())
            except (OSError, json.JSONDecodeError):
                existing = {}
            if existing.get("state") != "installing" or any(
                existing.get(key) != value for key, value in expected.items()
            ):
                raise SystemExit(
                    "Destination exists but is not a resumable managed Aurora workflow environment; "
                    "choose a new path to preserve it."
                )
            venv.EnvBuilder(with_pip=True).create(target)
            python_path = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        else:
            try:
                existing = json.loads(marker.read_text())
            except (OSError, json.JSONDecodeError):
                existing = {}
            if any(existing.get(key) != value for key, value in expected.items()):
                raise SystemExit(
                    "Managed environment does not match this dependency mode/lock; "
                    "choose a new path rather than modifying it."
                )
            if existing.get("state") == "ready":
                print(f"Already ready: {python_path}")
                return
            if existing.get("state") != "installing":
                raise SystemExit("Managed environment state is invalid; choose a new path.")
    else:
        target.mkdir(parents=True)
        marker.write_text(json.dumps({**expected, "state": "installing"}, indent=2, sort_keys=True) + "\n")
        venv.EnvBuilder(with_pip=True).create(target)
    python = str(python_path)

    def run(*cmd):
        subprocess.run([python, "-m", "pip", *cmd], check=True)

    if args.science:
        run("install", "torch==2.10.0", "torchvision==0.25.0", "--index-url", "https://download.pytorch.org/whl/cpu")
    requirements = {"light": "workflow-light.txt", "data": "workflow-data.txt",
                    "science": "workflow-cpu.txt"}[mode]
    run("install", "-r", str(repo / "requirements" / requirements))
    if not args.no_project:
        run("install", "--no-deps", "-e", str(repo))
    marker.write_text(json.dumps({**expected, "state": "ready"}, indent=2, sort_keys=True) + "\n")
    print(f"Ready: {python} -m aurora_workflow --help")


if __name__ == "__main__":
    main()
