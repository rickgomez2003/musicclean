# Recovery Alert Delivery SLOs

Orion 0.6.51 adds explicit delivery SLO evaluation.

- success rate: WARN below 99%, FAIL below 95%;
- retry rate: WARN above 10%, FAIL above 25%;
- terminal failure rate: WARN above 2%, FAIL above 5%;
- average delivery latency: WARN above 5 seconds, FAIL above 10 seconds.

At least four delivery samples are required before historical SLO status is authoritative. Before then the status is `INSUFFICIENT_DATA`.
