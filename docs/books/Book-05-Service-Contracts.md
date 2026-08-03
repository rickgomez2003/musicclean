# Book 05 — Service Contracts

**Status:** Active specification

`FilesystemObserver` is Orion's filesystem observation port. It yields
lightweight `FileObservation` values for a configured root.

The observer reports current state. The application synchronizer owns comparison
and persistence semantics.
