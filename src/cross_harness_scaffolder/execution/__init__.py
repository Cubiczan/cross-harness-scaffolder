"""Execution backends for validating harness output."""

from .base import ExecutionRequest, ExecutionResult
from .local import LocalExecutionBackend
from .superserve import SuperserveBackend, SuperserveConfig

__all__ = [
    "ExecutionRequest",
    "ExecutionResult",
    "LocalExecutionBackend",
    "SuperserveBackend",
    "SuperserveConfig",
]
