"""Local execution backend for trusted developer machines and CI."""
from __future__ import annotations

import subprocess

from .base import ExecutionRequest, ExecutionResult


class LocalExecutionBackend:
    backend_name = "local"

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        completed = subprocess.run(
            request.command,
            cwd=request.cwd,
            timeout=request.timeout_seconds,
            text=True,
            capture_output=True,
            check=False,
        )
        return ExecutionResult(
            ok=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            backend=self.backend_name,
        )
