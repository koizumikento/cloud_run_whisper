from __future__ import annotations

import argparse
import subprocess


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="apply ruff --fix and format")
    parser.add_argument("--html", action="store_true", help="emit html coverage report")
    args = parser.parse_args()

    # Ruff
    code = run(["uv", "run", "ruff", "check", "."])
    if code != 0 and args.fix:
        code = run(["uv", "run", "ruff", "check", ".", "--fix"])
        if code != 0:
            return code
        code = run(["uv", "run", "ruff", "format", "."])
        if code != 0:
            return code

    # Pytest with coverage
    if args.html:
        code = run(["uv", "run", "pytest", "--cov-report=html"])
    else:
        code = run(["uv", "run", "pytest"])  # addopts によりカバレッジ有効
    return code


if __name__ == "__main__":
    raise SystemExit(main())
