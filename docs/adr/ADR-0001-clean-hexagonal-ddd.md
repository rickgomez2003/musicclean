# ADR-0001: Clean + Hexagonal + Domain-Driven Architecture

- **Status:** Accepted
- **Date:** 2026-08-02

## Decision
Use DDD for language/boundaries, Hexagonal Architecture for ports/adapters, and Clean Architecture for dependency direction. Domain/application code does not directly depend on SQLite, Mutagen, FFmpeg, MusicBrainz, Discogs, Typer, or desktop frameworks.

## Consequences
Strong testability and replaceability at the cost of more explicit interfaces and mapping.
