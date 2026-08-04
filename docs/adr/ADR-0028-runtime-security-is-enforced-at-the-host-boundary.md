# ADR-0028: Runtime Security Is Enforced at the Host Boundary

Runtime HTTP security belongs in the host/runtime boundary, not in domain or
application code.

Controls include API-key authentication, trusted-host validation, explicit CORS
allowlists, security headers, request-size limits, and refusal of unauthenticated
non-local binding.
