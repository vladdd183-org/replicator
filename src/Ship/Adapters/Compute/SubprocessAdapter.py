# ruff: noqa: N999, I001
"""Вычисления через подпроцесс по ComputePort (L0)."""

from __future__ import annotations

import hashlib
import shlex
import time

import anyio

from src.Ship.Adapters.Errors import ComputeExecutionError, ComputeTimeoutError
from src.Ship.Adapters.Protocols import ComputePort  # noqa: F401
from src.Ship.Core.Errors import DomainException
from src.Ship.Core.Types import Identity, ComputeResult, Capability  # noqa: F401


class SubprocessComputeAdapter:
    """Запуск команды (function_id), stdin и таймаут через anyio.run_process."""

    async def execute(
        self,
        function_id: str,
        input_data: bytes,
        timeout_seconds: float = 60.0,
    ) -> ComputeResult:
        argv = shlex.split(function_id)
        if not argv:
            raise DomainException(
                ComputeExecutionError(
                    message="Empty command (function_id)",
                    function_id=function_id,
                    exit_code=-1,
                )
            )
        started = time.monotonic()
        try:
            with anyio.fail_after(timeout_seconds):
                proc = await anyio.run_process(argv, input=input_data)
        except TimeoutError:
            raise DomainException(
                ComputeTimeoutError(
                    message=f"Compute timeout for {function_id!r}",
                    function_id=function_id,
                    timeout_seconds=timeout_seconds,
                )
            ) from None
        duration_ms = int((time.monotonic() - started) * 1000)
        out = proc.stdout or b""
        if proc.returncode != 0:
            raise DomainException(
                ComputeExecutionError(
                    message=f"Command failed with exit code {proc.returncode}",
                    function_id=function_id,
                    exit_code=int(proc.returncode),
                )
            )
        digest = hashlib.sha256(out).hexdigest()
        return ComputeResult(
            output=out,
            output_id=digest,
            duration_ms=duration_ms,
            exit_code=int(proc.returncode),
        )
