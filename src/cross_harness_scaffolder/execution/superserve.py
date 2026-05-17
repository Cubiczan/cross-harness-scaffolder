"""SuperServe execution adapter descriptor.

SuperServe support is optional. The adapter keeps the interface stable while
allowing deployments to provide a concrete SuperServe client object.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import ExecutionRequest, ExecutionResult


@dataclass(frozen=True)
class SuperserveConfig:
    template: str = "python-dev"
    network_policy: str = "deny-by-default"
    destroy_after_run: bool = True


class SuperserveBackend:
    backend_name = "superserve"

    def __init__(self, client: object, config: SuperserveConfig | None = None) -> None:
        self.client = client
        self.config = config or SuperserveConfig()

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        create = getattr(self.client, "create_sandbox", None)
        run_command = getattr(self.client, "run_command", None)
        destroy = getattr(self.client, "destroy_sandbox", None)
        if create is None or run_command is None:
            raise RuntimeError("SuperServe client must expose create_sandbox() and run_command()")

        sandbox = create(template=self.config.template, network_policy=request.network_policy or self.config.network_policy)
        sandbox_id = getattr(sandbox, "id", str(sandbox))
        try:
            result = run_command(sandbox_id=sandbox_id, command=list(request.command), timeout_seconds=request.timeout_seconds)
            exit_code = int(getattr(result, "exit_code", 0))
            stdout = str(getattr(result, "stdout", ""))
            stderr = str(getattr(result, "stderr", ""))
            return ExecutionResult(
                ok=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                backend=self.backend_name,
                sandbox_id=sandbox_id,
            )
        finally:
            if self.config.destroy_after_run and destroy is not None:
                destroy(sandbox_id=sandbox_id)
