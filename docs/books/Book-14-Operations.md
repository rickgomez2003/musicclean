# Book 14 — Operations

**Status:** Active specification

## Runtime composition

0.6.21 introduces Orion's runtime composition root.

```text
RuntimeConfig
     ↓
SQLite Migration
     ↓
LocalFilesystemMutator
     ↓
UtcSystemClock
     ↓
SqliteUnitOfWork Factory
     ↓
OrionService
     ↓
FastAPI Host
     ↓
Uvicorn
```

## Launch

```powershell
python -m musicclean.orion.runtime `
    --database .\orion.db `
    --host 127.0.0.1 `
    --port 8765
```

The default listener is localhost-only.

## Environment configuration

Supported environment variables:

- `MUSICCLEAN_ORION_DATABASE`
- `MUSICCLEAN_ORION_HOST`
- `MUSICCLEAN_ORION_PORT`
- `MUSICCLEAN_ORION_LOG_LEVEL`
- `MUSICCLEAN_ORION_STARTUP_RECONCILE`

## Startup sequence

Before serving HTTP, runtime bootstrap:

1. creates the database parent directory when required;
2. connects to SQLite;
3. applies all Orion migrations;
4. verifies the resulting schema version;
5. constructs concrete adapters;
6. constructs `OrionService`;
7. optionally performs the detection-only startup reconciliation sweep;
8. constructs the FastAPI application.

No recovery action is automatically approved or applied during startup.
