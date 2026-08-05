# Recovery Objectives & SLOs

Orion evaluates recovery drill evidence against explicit recovery objectives.

## Default policy

| Metric | PASS | WARN | FAIL |
|---|---:|---:|---:|
| Recovery duration | <= 720 s | >720 and <=900 s | >900 s |
| Last successful drill age | <=10 d | >10 and <=14 d | >14 d |
| Successful drill ratio | >=98% | >=95% and <98% | <95% |

SLO evaluation is combined with historical trend evidence to feed the
provider-neutral alert policy introduced in 0.6.47.
