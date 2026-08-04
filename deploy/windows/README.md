# Windows deployment

Use a dedicated service account with read/write access only to the configured
Orion database, log, and telemetry directories.

`Install-Orion.ps1` provisions the runtime environment and is safe to rerun.
`Start-Orion.ps1` remains the service-wrapper entrypoint.

Register `Start-Orion.ps1` with the organization's preferred Windows service
manager or scheduled-service tooling.

Do not place the API key directly in either script. Supply runtime
configuration through the service environment.

After service startup, verify:

`http://127.0.0.1:8765/v1/health`
