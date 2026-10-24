import json
import os
import subprocess
import time

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("WHISPER_SMOKE_IMAGE"),
    reason="set WHISPER_SMOKE_IMAGE to a local smoke image",
)


def test_setup_cuda_syntax():
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--network",
            "none",
            "--entrypoint",
            "bash",
            os.environ["WHISPER_SMOKE_IMAGE"],
            "-n",
            "/app/scripts/setup_cuda.sh",
        ],
        check=True,
        timeout=30,
    )


def test_cuda_cleanup_preserves_distribution_keyrings():
    # Stub package/download commands; run real cleanup only inside a disposable container.
    probe = """
import os
import subprocess
import tempfile
from pathlib import Path

keyrings = Path('/usr/share/keyrings')
before = {p: p.read_bytes() for p in keyrings.glob('*.gpg')}
assert any('debian' in p.name for p in before)
sources = [
    Path('/var/cuda-repo-debian12-12-9-local/cuda-smoke-keyring.gpg'),
    Path('/var/cudnn-local-repo-debian12-9.10.1/cudnn-smoke-keyring.gpg'),
]
for source in sources:
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b'NVIDIA keyring fixture')
with tempfile.TemporaryDirectory() as directory:
    for name in ('apt-get', 'apt', 'wget', 'dpkg'):
        stub = Path(directory, name)
        stub.write_text('#!/bin/sh\\nexit 0\\n')
        stub.chmod(0o755)
    env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'])
    subprocess.run(['bash', '/app/scripts/setup_cuda.sh'], check=True, env=env)
assert all(p.read_bytes() == content for p, content in before.items())
assert all(not (keyrings / source.name).exists() for source in sources)
"""
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--network",
            "none",
            "--entrypoint",
            "python",
            os.environ["WHISPER_SMOKE_IMAGE"],
            "-c",
            probe,
        ],
        check=True,
        timeout=30,
    )


def test_container_startup():
    container = subprocess.check_output(
        [
            "docker",
            "run",
            "--detach",
            "--pull=never",
            "--network",
            "none",
            "--env",
            "WHISPER_SKIP_LOAD=1",
            os.environ["WHISPER_SMOKE_IMAGE"],
        ],
        text=True,
        timeout=30,
    ).strip()
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            probe = subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "python",
                    "-c",
                    "import urllib.request; "
                    "response = urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=1); "
                    "print(response.read().decode())",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if probe.returncode == 0:
                assert json.loads(probe.stdout)["status"] == "ok"
                return
            time.sleep(0.25)
        logs = subprocess.check_output(["docker", "logs", container], stderr=subprocess.STDOUT)
        pytest.fail(logs.decode())
    finally:
        subprocess.run(["docker", "rm", "--force", container], check=True, capture_output=True)
