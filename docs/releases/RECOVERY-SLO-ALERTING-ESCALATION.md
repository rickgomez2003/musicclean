# Recovery SLO Alerting & Escalation

Orion 0.6.47 converts SLO and trend evidence into structured operational alerts.

## Severity policy

| Condition | Severity |
|---|---|
| SLO PASS + non-worsening trend | no alert |
| SLO WARN | ADVISORY |
| SLO FAIL | CRITICAL |
| WORSENING duration trend | ADVISORY |
| 2 consecutive failed drills | ESCALATED |

The alert record also carries a 24-hour suppression-window value for future
delivery providers.

## Outputs

- `recovery-slo-alert.json`
- `recovery-slo-alert-summary.md`

The summary is appended to the GitHub Actions step summary. No external
notification provider is enabled in 0.6.47.
