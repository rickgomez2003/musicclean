# Coding Standards

- Python 3.12+.
- Type public APIs.
- Ruff, MyPy, and Pytest are mandatory quality gates.
- Prefer explicit domain types over unstructured dictionaries.
- Domain modules have no infrastructure imports.
- Use `pathlib.Path` at filesystem boundaries.
- Avoid broad exception handling except at explicit boundaries.

## Dependency rule
Allowed: application→domain/ports; adapters→ports/domain; apps→application.
Forbidden: domain→adapters/infrastructure/UI; ports→concrete adapters.
