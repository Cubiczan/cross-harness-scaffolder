import sys

from cross_harness_scaffolder import (
    CockroachStore,
    ExecutionRequest,
    LocalExecutionBackend,
    PayloadRecord,
    RoundEventRecord,
    SQLiteStore,
    StorageCapability,
    SuperserveBackend,
    SuperserveConfig,
    build_database_config,
    cockroach_retry_delays,
    content_hash,
)


def test_database_config_supports_sqlite_postgres_and_cockroach() -> None:
    sqlite = build_database_config("sqlite:///runs/chs.db")
    postgres = build_database_config("postgresql://user:pass@localhost:5432/chs")
    cockroach = build_database_config("cockroachdb://user:pass@localhost:26257/chs?sslmode=require")

    assert sqlite.capability == StorageCapability.SQLITE_LOCAL
    assert not sqlite.requires_external_dependency
    assert postgres.capability == StorageCapability.POSTGRES_SHARED
    assert postgres.requires_external_dependency
    assert cockroach.capability == StorageCapability.COCKROACH_DISTRIBUTED
    assert cockroach.query["sslmode"] == ("require",)


def test_sqlite_store_initializes_and_writes_payload_and_event(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "chs.db")
    payload_body = "BEGIN_PAYLOAD [RX] [ABC123]\nhello\nEND_PAYLOAD [RX] [ABC123]"
    payload = PayloadRecord(content_hash=content_hash(payload_body), body=payload_body, token_estimate=8)

    assert store.initialize().ok
    assert store.put_payload_blob(payload).ok
    assert store.append_round_event(
        RoundEventRecord(
            event_id="evt-1",
            session_id="session-1",
            phase=0,
            round_number=0,
            route="RX",
            payload_id="ABC123",
            content_hash=payload.content_hash,
            payload_echo="[RX] [ABC123] CONFIRMED",
            status_snapshot="{}",
        )
    ).ok


def test_cockroach_retry_delays_are_exponential() -> None:
    assert cockroach_retry_delays(max_attempts=4, base_seconds=0.1) == (0.1, 0.2, 0.4, 0.8)


def test_cockroach_retry_retries_restart_transaction() -> None:
    attempts = {"count": 0}

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise Exception("restart transaction: 40001")
        return "ok"

    assert CockroachStore("cockroachdb://localhost:26257/chs").run_with_retry(flaky) == "ok"
    assert attempts["count"] == 3


def test_local_execution_backend_runs_command() -> None:
    backend = LocalExecutionBackend()
    result = backend.run(ExecutionRequest(command=(sys.executable, "-c", "print('ok')")))

    assert result.ok
    assert result.exit_code == 0
    assert result.stdout.strip() == "ok"
    assert result.backend == "local"


class _FakeSandbox:
    id = "sandbox-1"


class _FakeResult:
    exit_code = 0
    stdout = "sandbox ok"
    stderr = ""


class _FakeSuperserveClient:
    def __init__(self) -> None:
        self.destroyed = False
        self.created_with = None
        self.ran_with = None

    def create_sandbox(self, *, template: str, network_policy: str):
        self.created_with = (template, network_policy)
        return _FakeSandbox()

    def run_command(self, *, sandbox_id: str, command: list[str], timeout_seconds: int):
        self.ran_with = (sandbox_id, command, timeout_seconds)
        return _FakeResult()

    def destroy_sandbox(self, *, sandbox_id: str) -> None:
        self.destroyed = sandbox_id == "sandbox-1"


def test_superserve_backend_uses_client_contract() -> None:
    client = _FakeSuperserveClient()
    backend = SuperserveBackend(client, SuperserveConfig(template="python-dev", network_policy="deny"))

    result = backend.run(ExecutionRequest(command=("pytest", "-q"), timeout_seconds=30))

    assert result.ok
    assert result.backend == "superserve"
    assert result.sandbox_id == "sandbox-1"
    assert client.created_with == ("python-dev", "deny")
    assert client.ran_with == ("sandbox-1", ["pytest", "-q"], 30)
    assert client.destroyed
