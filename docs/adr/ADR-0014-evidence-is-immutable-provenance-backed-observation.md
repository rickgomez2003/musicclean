# ADR-0014: Evidence Is an Immutable, Provenance-Backed Observation

- **Status:** Accepted
- **Date:** 2026-08-03

Evidence is stored separately from domain entities and from inferred Knowledge.

Each Evidence record identifies:
- subject;
- observation kind;
- typed value;
- provider;
- provider version when known;
- observation timestamp;
- warning/recovery context when present.

Evidence is append-oriented. New observations do not silently rewrite historical
observations. Knowledge rules may later choose which evidence is current or most
trustworthy.
