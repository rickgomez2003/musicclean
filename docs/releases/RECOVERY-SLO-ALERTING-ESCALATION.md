# Recovery SLO Alerting & Escalation

Orion converts SLO and trend evidence into structured operational alerts.

## Severity policy

| Condition | Severity |
|---|---|
| SLO PASS + non-worsening trend | no alert |
| SLO WARN | ADVISORY |
| SLO FAIL | CRITICAL |
| WORSENING duration trend | ADVISORY |
| 2 consecutive failed drills | ESCALATED |

0.6.48 enables external delivery through a signed generic HTTPS webhook.
Healthy/no-alert records do not generate external requests.
