# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version. Published tags are immutable.

## Recovery operations

0.6.52 adds bounded, deduplicated, read-only history and trend analysis for
recovery alert delivery SLO evidence.

## Post-release verification

Post-release verification validates actual published artifacts.\n\n## Recovery alert delivery SLO alerting\n\n0.6.53 emits a provider-neutral alert decision without new write privileges.\n\n\n## Recovery alert delivery SLO routing\n\n0.6.54 emits route decision evidence without adding external delivery or repository mutation privileges.\n

## Recovery alert routed delivery

0.6.55 performs signed route-specific webhook delivery and retains a secret-safe delivery receipt with recovery drill evidence.

## Routed recovery alert delivery resilience

0.6.56 verifies bounded retry policy, route preservation, stable delivery identity, and secret-safe attempt history.

## Routed recovery alert delivery observability

0.6.57 generates and verifies secret-safe routed-delivery observability artifacts and publishes the summary with recovery drill evidence.

## Routed recovery alert delivery SLOs

0.6.58 evaluates and verifies secret-safe, policy-driven routed-delivery SLO evidence during recovery drills.

## Routed recovery alert delivery SLO history and trends

0.6.59 builds bounded, deduplicated routed-delivery SLO history and verifies secret-safe trend evidence during recovery drills.

## Routed recovery alert delivery SLO alerting

0.6.60 builds and verifies provider-neutral routed-delivery SLO alert evidence while keeping external delivery disabled.

## Routed recovery alert delivery SLO escalation and routing

0.6.61 builds and verifies provider-neutral SLO routing evidence before any future external-delivery layer is permitted.

## Routed recovery SLO alert delivery

0.6.62 performs route-specific HTTPS delivery for routed SLO alerts, using HMAC-SHA256 signatures and secret-safe receipt evidence.

## Routed SLO alert delivery resilience

0.6.63 applies bounded retry policy and retains secret-safe per-attempt evidence.

## Routed SLO alert delivery observability

0.6.64 builds and verifies bounded, secret-safe routed SLO delivery observability.

## Routed SLO alert delivery SLOs

0.6.65 evaluates and verifies routed SLO alert delivery SLO evidence before release validation.

## Routed SLO alert delivery SLO history and trends

0.6.66 builds, verifies, and retains bounded secret-safe SLO history and trend evidence before release validation.

## Routed SLO alert delivery SLO alerting

0.6.67 builds and verifies provider-neutral routed SLO delivery SLO alert evidence before release validation.

## Routed SLO alert delivery SLO escalation and routing

0.6.68 builds and verifies provider-neutral routed SLO delivery SLO route evidence before release validation.

## Routed SLO alert delivery routed delivery

0.6.69 performs route-specific signed webhook delivery and verifies secret-safe delivery receipts before release validation.

## Routed SLO alert delivery routed-delivery resilience

0.6.70 verifies bounded retry policy and secret-safe resilient delivery receipts before controlled release validation.

## Routed SLO alert delivery routed-delivery observability

0.6.71 builds and verifies bounded, secret-safe routed-delivery observability evidence before controlled release validation.

## Routed SLO alert delivery routed-delivery SLOs

0.6.72 evaluates and verifies policy-driven routed-delivery SLO evidence before controlled release validation.

## Routed SLO alert delivery routed-delivery SLO history and trends

0.6.73 builds bounded history, analyzes read-only trends, and verifies secret-safe trend evidence before controlled release validation.
