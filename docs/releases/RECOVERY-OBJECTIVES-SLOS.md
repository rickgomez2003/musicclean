# Recovery Objectives & SLOs

Orion 0.6.45 evaluates recovery drill evidence against explicit recovery
objectives.

## Default policy

| Metric | PASS | WARN | FAIL |
|---|---:|---:|---:|
| Recovery duration | <= 720 s | >720 and <=900 s | >900 s |
| Last successful drill age | <=10 d | >10 and <=14 d | >14 d |
| Successful drill ratio | >=98% | >=95% and <98% | <95% |

Success-ratio evaluation requires at least four drill samples. Until that
minimum is available, the metric reports WARN rather than claiming compliance.

## Output

`recovery-slo-report.json` records:

- evaluation timestamp;
- overall PASS/WARN/FAIL;
- latest drill identity;
- recovery duration measurement;
- successful-drill age;
- successful-drill ratio;
- warning/objective thresholds;
- sample count.

The policy values are operational defaults and may be tightened later as
measured recovery performance becomes established.
