# Recovery SLO History & Trend Analysis

Orion 0.6.46 persists recovery context across workflow runs by reading prior
Recovery Drill artifacts.

## History policy

- maximum retained analytical records: 52;
- artifact lookup depth: 52 completed workflow runs;
- de-duplication key: `drill_id`;
- chronological sort key: `completed_at`;
- short rolling window: 4 drills;
- long rolling window: 12 drills;
- minimum samples for duration direction: 4.

## Trend evidence

`recovery-slo-trend.json` records:

- available history count;
- latest drill identity;
- short-window success ratio;
- short-window average recovery duration;
- long-window success ratio;
- long-window average recovery duration;
- duration trend: IMPROVING, STABLE, WORSENING, or INSUFFICIENT_DATA.

History retrieval requires `actions: read` only. It does not grant release
mutation permissions.
