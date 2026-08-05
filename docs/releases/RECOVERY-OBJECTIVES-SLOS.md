# Recovery Objectives & SLOs

Orion evaluates recovery drill evidence against explicit recovery objectives.

## Default policy

| Metric | PASS | WARN | FAIL |
|---|---:|---:|---:|
| Recovery duration | <= 720 s | >720 and <=900 s | >900 s |
| Last successful drill age | <=10 d | >10 and <=14 d | >14 d |
| Successful drill ratio | >=98% | >=95% and <98% | <95% |

Success-ratio evaluation requires at least four drill samples. 0.6.46 supplies
that history from prior Recovery Drill artifacts when sufficient runs exist.

`recovery-slo-report.json` contains point-in-time SLO evaluation, while
`recovery-slo-trend.json` contains rolling historical analysis.
