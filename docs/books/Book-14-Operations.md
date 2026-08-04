# Book 14 — Operations

0.6.27 adds deployment automation over the existing runtime packaging layer.

Automation now covers:

- Linux installation/update with systemd;
- Windows runtime provisioning;
- deployment preflight validation;
- post-start health verification;
- Docker build validation in CI.

Deployment scripts are intended to be idempotent. Existing configuration is
preserved where possible, and a deployment is not considered successful until
the Orion health endpoint responds successfully.
