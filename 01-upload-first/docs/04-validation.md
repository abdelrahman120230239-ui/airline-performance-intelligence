# 4. Validation

## Verified against BTS files

The independent reconciliation read each archived flight CSV and counted the same business outcomes from the signed delays and flags. Checksums matched the four manifests. The source audit covered 2,111,123 rows, 15 reporting carrier certificates, 341 airport IDs and 6,108 directional airport-code pairs. There were zero duplicate candidate-key rows or duplicate projected rows. The candidate key was flight date, carrier ID, flight number, origin ID, destination ID and scheduled local departure HHMM.

| Profile check | Result |
|---|---:|
| Comparable arrivals | 2,059,384 |
| Signed arrival delays absent | 51,739 |
| Signed departure delays absent | 45,796 |
| Completed flights missing arrival delay | 0 |
| Non-cancelled flights missing departure delay | 0 |
| Cancelled flights with missing or invalid reason | 0 |
| BTS 15+ indicator disagreements in eligible rows | 0 |
| Eligible late arrivals with incomplete cause fields | 0 |
| Eligible late arrivals whose cause fields fail to sum to signed delay | 0 |

The 51,739 missing arrivals are the 47,108 cancellations and 4,631 diversions. Non-cancelled flights all have signed departure delay. Some cancelled rows also report departure delay, so the departure denominator explicitly applies the cancellation flag.

| BTS month | Scheduled | Comparable arrivals | On time | Late 15+ | Cancelled | Diverted | Late minutes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-01 | 547,271 | 525,370 | 398,960 | 126,410 | 20,389 | 1,512 | 9,538,664 |
| 2024-02 | 519,221 | 515,269 | 433,233 | 82,036 | 3,002 | 950 | 5,257,296 |
| 2025-01 | 539,747 | 522,269 | 424,139 | 98,130 | 16,312 | 1,166 | 6,943,994 |
| 2025-02 | 504,884 | 496,476 | 393,374 | 103,102 | 7,405 | 1,003 | 7,411,011 |

See the [field-level audit](source-profile.csv), [reconciliation](monthly-reconciliation.csv) and [reproducible profiling script](../scripts/profile_bts.py).

## Manual checks and corresponding Desktop queries

1. **Scheduled and completed flight grain.** Select AA, JFK as origin, LAX as destination and January 1, 2025. The [nine source records](manual-route-fixture.csv) have signed arrival delays of −10, −7, −33, −29, −28, −22, −15, −9 and −2. All nine completed and qualify as on time. Scheduled = 9, comparable = 9, on-time rate = 9 ÷ 9 = 100%, and late, cancelled and late minutes each equal 0. Swapping the two airport roles must change the grain to LAX → JFK.
2. **Threshold and exclusion.** The [four BTS samples](manual-threshold-fixture.csv) have +14, +15, cancelled, and diverted outcomes. Scheduled = 4. The first two qualify, of which only +14 is on time. OTP = 1 ÷ 2 = 50%. Cancellation rate and diversion rate are each 1 ÷ 4 = 25%. Total late minutes and attributed cause minutes each equal 15.
3. **Weighted rates.** For Jan–Feb 2025, add 424,139 + 393,374 on-time arrivals and 522,269 + 496,476 comparable arrivals. Divide 817,513 by 1,018,745 to get 80.2471%. Under an AA selection the visible AA rate is 112,895 ÷ 140,890 = 80.13%, while the unrestricted benchmark retains 80.2471% unless RLS is applied.
4. **Time intelligence.** In February 2025, Scheduled YTD should include January and February and return 1,044,631. For matched February, subtract February 29, 2024 (19,105 scheduled, 19,002 comparable, 16,090 on time) from the 2024-02 baseline. Prior scheduled = 500,116 and prior OTP = 417,143 ÷ 496,267 = 84.0562%. Current OTP = 393,374 ÷ 496,476 = 79.2332%, so YoY is −4.82 pp. January and February together yield +0.37 pp on matched days. A March-only selection in DAX Query View should return blank rates.
5. **Rank and filter context.** With Jan–Feb 2025 and all carriers selected, expect HA rank 1, WN rank 2 and OH rank 14. Select only WN and OH and expect ranks 1 and 2. Shrink the selection to a date/route slice with fewer than 1,000 comparable arrivals and expect no carrier rank. When comparing January and February, keep rates weighted by the flight counts.
6. **RLS and interactions.** Use the test matrix in [Report implementation and access](03-report-and-security.md) and check the two-way bookmark toggle, tooltip counts, and drill-through route and dates.

For a pass/fail run, paste the entire [Desktop acceptance query](desktop-acceptance.dax) into Power BI Desktop DAX Query View after a full refresh with CarrierViewer and Other user cleared. It should return 81 PASS rows. It checks monthly counts and rates, the two manual fixtures, the weighted network benchmark, February leap-day alignment and YTD behavior, and uncovered months. [validation.dax](validation.dax) provides shorter reconciliation queries to inspect the actual measures. Run the visible interaction and RLS checks separately. Reconciliation and manual arithmetic use the raw data. Microsoft's Power Query parser accepted all 16 M queries. The Tabular Object Model loaded the TMDL and confirmed the 10 Import tables, six active relationships, 47 measures and the RLS role. All 85 schema-bearing PBIP and PBIR documents matched Microsoft's published schemas. Report field bindings and navigation and bookmark references passed static checks. Desktop refresh, DAX evaluation and visual interaction tests require a Windows Power BI Desktop session.
