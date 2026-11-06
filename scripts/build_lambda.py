"""Build a Linux-compatible, self-contained Lambda zip without deploying it."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


def install_linux_dependencies(root: Path, target: Path) -> None:
    requirements = root / "lambda" / "requirements.txt"
    if importlib.util.find_spec("pip"):
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            str(target),
            "--platform",
            "manylinux2014_x86_64",
            "--implementation",
            "cp",
            "--python-version",
            "3.12",
            "--only-binary=:all:",
            "--requirement",
            str(requirements),
        ]
    else:
        command = [
            "uv",
            "pip",
            "install",
            "--target",
            str(target),
            "--python-platform",
            "x86_64-manylinux2014",
            "--only-binary=:all:",
            "--requirement",
            str(requirements),
        ]
    subprocess.run(command, check=True)


root = Path(__file__).resolve().parents[1]
target = root / "artifacts" / "fulfilliq-lambda"
archive = root / "artifacts" / "fulfilliq-lambda"
if target.exists():
    shutil.rmtree(target)
target.mkdir(parents=True)
shutil.copy2(root / "lambda" / "handler.py", target / "handler.py")
shutil.copytree(root / "src" / "fulfilliq", target / "fulfilliq")
install_linux_dependencies(root, target)
shutil.make_archive(str(archive), "zip", target)
print(f"created Linux-compatible {archive}.zip")
