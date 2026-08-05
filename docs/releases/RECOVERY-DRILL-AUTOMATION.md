# Recovery Drill Automation

The Orion Recovery Drill proves durable archive recovery, evaluates SLOs,
computes historical trends, and generates provider-neutral alert evidence.

0.6.49 separates webhook delivery from the recovery job. The recovery job
uploads a short-lived alert handoff artifact; a dedicated downstream job
performs external delivery without inheriting AWS OIDC capability.
