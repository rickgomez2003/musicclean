# Orion Architecture

Orion combines Domain-Driven Design, Hexagonal Architecture, Clean Architecture dependency direction, and specification-driven development.

```mermaid
flowchart TB
 Apps[CLI / Desktop / REST / Server] --> Application
 Application --> Domain
 Application --> Ports
 Adapters --> Ports
 Adapters --> Domain
 Infrastructure --> Adapters
```

The domain must not import SQLite, Mutagen, FFmpeg, HTTP clients, Typer, or UI frameworks.
