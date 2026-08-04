# Windows deployment

Use a dedicated service account with read/write access only to the configured
Orion database, log, and telemetry directories.

`Start-Orion.ps1` is the service-wrapper entrypoint. Register it with the
organization's preferred Windows service manager or scheduled-service tooling.

Do not place the API key directly in the wrapper script. Supply runtime
configuration through the service environment.
