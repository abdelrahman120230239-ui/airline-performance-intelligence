# 1. Requirements and dimensional model

| Stakeholder | Decision | Questions | Page |
|---|---|---|---|
| COO and executives | Set the weekly operations review agenda | Is arrival reliability improving? How many flights are represented? | Executive Overview |
| Airline performance team | Select operations to benchmark | Which reporting carriers lead or lag? How does each compare with the weighted network in the same date and airport scope? | Airline Benchmarking |
| Network planners and station managers | Select routes and stations for review | Where are delays frequent or severe? How does an airport perform in each role? | Airport and Route Analysis |
| Operations control | Triage disruptions and inspect records | Which categories were reported? Which flight records contribute to a route's result? | Delay and Cancellation Investigation and flight drill-through |
| BI owner | Govern refresh and access | Which months loaded? How many rows were excluded from each denominator? Is carrier access enforced? | Model and validation |

**Scope.** BTS Reporting Carrier On-Time Performance for January–February 2024 and January–February 2025. The population is reported domestic scheduled segments. Each row represents a segment in the reporting data, including cancelled and diverted records. Use the reporting carrier certificate and the BTS scheduled flight date. Routes are directional pairs of scheduled airports.

**Acceptance criteria.** Reconcile every source month and the manual drill-through fixture. Show counts alongside rates. Preserve month, geography and carrier context when drilling through. Use a weighted network benchmark. Suppress carrier ranks below 1,000 comparable arrivals and route ranks below 500. Test independent airport-role filters and their intersection. Keep the date table contiguous across months without files.

## Star schema

| Table | Grain and key | Main attributes |
|---|---|---|
| FactFlight | One BTS scheduled segment per ingested row. Technical row ID is YYYYMM × 10,000,000 plus the 1-based source row ordinal | Date, carrier, origin, destination, route, cancellation reason, flags, flight number, scheduled local times, signed delays and reported cause minutes |
| DimDate | One day, Date | Year, month, weekday and source coverage |
| DimCarrier | One reporting carrier certificate, CarrierID | Latest observed reporting code and unique display label |
| DimOriginAirport | One scheduled-origin airport, AirportID | Code, city, state and unique display label |
| DimDestinationAirport | One scheduled-destination airport, AirportID | Same airport catalog, independent report role |
| DimRoute | One ordered pair, RouteID | Directional display label |
| DimCancellation | One reason key, CancellationKey | A, B, C, D, unknown and not applicable |
| DimDelayCause | Disconnected list of five cause groups | Label and sort order used by DAX to select matching fact columns |
| CarrierAccess | Disconnected, hidden sample entitlements | Lower-case UPN and carrier ID. Role explicitly filters this table and DimCarrier |
| FlightMetrics | Hidden placeholder column | DAX measures organized into display folders |

All six relationships are active one-to-many with single-direction filtering from dimension to fact. The two airport roles and route dimension each reach the fact directly. The shared catalog is a load-disabled Power Query expression. Airport and carrier attributes are Type 1. Latest observations win, with deterministic tie-breaks. Source revisions can change ordinals. Use ReportMonth and SourceRowID as trace evidence.

RouteID uses OriginAirportID × 1,000,000 + DestinationAirportID. The pipeline rejects airport IDs outside 1–999,999. Labels include IDs for disambiguation. Carrier RLS filters the fact through DimCarrier. The remaining dimensions contain public labels and can be visible across carriers.

## Power BI Desktop implementation

1. Start with the manifest and the contract in [Power Query](02-power-query.md). Review the denominator rules in the [KPI dictionary](kpi-dictionary.csv).
2. Open the PBIP. In Model view confirm six active relationships and their directions. Under Table tools, confirm or mark DimDate as the date table using Date.
3. Verify Year Month sorts by YearMonthKey, Weekday by WeekdayNumber, and delay causes by CauseOrder. Keep automatic date/time off. Turn off automatic relationship detection if adding tables.
4. Reconcile the fixtures and test RLS before tuning visuals.

Sources [BTS field definitions](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ), [Microsoft star schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema), [Microsoft active relationship guidance](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-active-inactive).
