# Infrastructure Support

Cross-Harness Scaffolder now has explicit infrastructure seams for storage and execution.

## Storage Backends

The storage layer starts with a shared URL parser and backend descriptors:

- `sqlite:///runs/chs.db` for local development and single-user runs.
- `postgresql://user:pass@host:5432/chs` for shared production state.
- `cockroachdb://user:pass@host:26257/chs?sslmode=require` for distributed production state.

### SQLite

`SQLiteStore` uses Python's standard `sqlite3` module and the core schema. It is intended for:

- local runs,
- test fixtures,
- single-user audit bundles,
- quick demos.

### PostgreSQL

`PostgresStore` keeps `psycopg` optional. It exposes migration SQL and a `connect()` method once the `postgres` extra is installed.

Recommended use:

- shared team sessions,
- concurrent harness writers,
- JSON-heavy audit reporting,
- hosted dashboards.

### CockroachDB

`CockroachStore` uses the same optional `psycopg` dependency, but adds serializable retry guidance through `run_with_retry()` and `cockroach_retry_delays()`.

Recommended use:

- distributed teams,
- regional resilience,
- high-availability audit state,
- production lock records that must survive node failure.

## Execution Backends

Execution backends validate harness output without making the core package own tools or secrets.

### LocalExecutionBackend

Runs trusted commands on a developer machine or CI runner.

Use for:

- local tests,
- compile checks,
- static analysis,
- package builds.

### SuperserveBackend

`SuperserveBackend` is an adapter for SuperServe-style Firecracker microVM execution. The package accepts a client object instead of hard-coding a vendor SDK so deployments can pin their preferred SuperServe client.

Use for:

- untrusted harness output,
- isolated code execution,
- network-deny validation,
- ephemeral test environments,
- sandbox IDs attached to audit events.

The harness registry also exposes `SuperServe` as a profile through aliases such as `firecracker`, `microvm`, and `superserve.ai`. Use that profile when a session needs sandbox validation as a first-class validator rather than only an execution backend.

The adapter expects the client to expose:

- `create_sandbox(template=..., network_policy=...)`
- `run_command(sandbox_id=..., command=..., timeout_seconds=...)`
- optional `destroy_sandbox(sandbox_id=...)`

## Design Rule

The core package stays dependency-light. Database drivers and sandbox SDKs are optional, while interfaces, schemas, and deterministic tests remain available everywhere.
