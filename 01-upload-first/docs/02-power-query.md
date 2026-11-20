# 2. Power Query and data quality

## Reproduce the refresh

The repository stages the CSVs locally in data/raw. The README setup downloads
the four archives, verifies their SHA-256 values, and sets the model's data
folder. If you prefer to set up the data manually, use the steps below.

1. Run the README download command or use the [BTS PREZIP directory](https://www.transtats.bts.gov/PREZIP/). Download the four Reporting Carrier ZIPs from the [source manifest](source-manifest.csv). For a manual setup, extract the single flight CSV in each ZIP and rename each to YYYY-MM.csv.
2. Open the PBIP in Power BI Desktop. Use Transform data > Manage parameters to set pRawFolder to the absolute Windows folder that contains the four CSVs. The parameter expects a folder path. Allow local file access if prompted.
3. Check SourceMonths and preview FactFlight. For profiling in Desktop, enable Column quality, Column distribution and Column profile under View. Set profiling to the entire dataset when checking counts.
4. Close & Apply, then Refresh. Reconcile to [source-profile.csv](source-profile.csv) and [monthly-reconciliation.csv](monthly-reconciliation.csv). Reassess checksums and the audit if a source archive is revised.

## Build the queries in a blank Desktop file

In Transform data, create a Blank Query for each file in the [Power Query source](../power-query/). Name each query after its file stem and paste the file contents into Advanced Editor. Create pRawFolder, SourceMonths, fxReadMonth, stgFlights, fxLatest and AirportCatalog first, in that order. Keep load disabled for these supporting expressions. Create FactFlight and the dimensions next. Load the final tables and use Model view to create the six Date, Carrier, Origin Airport, Destination Airport, Route and Cancellation relationships listed in the [model brief](01-requirements-and-model.md). Mark DimDate using its Date column. Use Modeling > New measure or TMDL view to install the [measure library](measure-library.dax) under FlightMetrics.

## Transformation contract

| Query | Transformation and handling |
|---|---|
| pRawFolder and SourceMonths | Control the exact folder and four-month manifest. Missing files raise File.Contents errors, so refresh cannot silently omit a file. |
| fxReadMonth | Opens the CSV with quoting and Windows-1252 encoding. Keeps named columns and fails on a missing required header. Trims text while retaining scheduled local HHMM and flight number as text. Parses dates explicitly and signed minute and key fields as whole numbers with en-US culture. Rejects invalid grain, keys, flags, month or source ordinal. |
| stgFlights | Appends the required months and derives the integer directional RouteID. Load disabled. |
| FactFlight | Renames fields, retains null delays and cause minutes, derives arrival and departure outcomes and a cause-coverage flag. Missing or unexpected cancellation code on a cancelled record maps to Unknown or missing. Remaining records map to Not applicable. |
| fxLatest, AirportCatalog and dimensions | Build unique entities from recent observations. Airport catalog combines both roles before resolution. Route labels use both airport roles. Only final dimensions load. |
| DimDate | Builds a contiguous 2024–2025 calendar, labels source-covered months, and provides chronological sort columns. |
| DimCancellation, DimDelayCause and CarrierAccess | Small, typed lookup tables with explicit domain values or fictitious sample principals. |

The independent profile compares signed minutes to the BTS 15+ indicators, checks candidate duplicates and source nulls, and reconciles the sum of the five reported cause fields to the signed arrival delay on eligible late flights. The model preserves the BTS reporting grain. It retains early arrivals and departures as negative minutes and distinguishes blanks from zero. For delays by cause, it sums only observed minutes on eligible arrivals delayed 15 minutes or more. A zero field is a reported zero. A blank field has no attributed minutes. The cause coverage KPI counts any nonblank cause field. The data profile separately counts partial and missing fields.

The BTS reporting directive distinguishes airline-reported attribution from an independent operational root-cause analysis. Cancellation reason and delay-minute attribution are different measures. Local clock values retain their source meaning across time zones, and delay calculations use the BTS signed minute columns. Use the scheduled BTS flight date for grouping.

## Scope maintenance and performance

Update SourceMonths and the download manifest together when adding data. Recheck identifier bounds, reporting population, duplicate candidates and type changes. Early projection, integer keys, hidden technical fields, explicit measures, and a shared airport catalog limit model size and ambiguity. The folder workflow uses Import and has no query folding. Keep the workspace on a local disk while refreshing. For materially larger histories, move ingestion to a partitioned or foldable source before using incremental refresh. Record Desktop refresh duration, PBIX size, and representative DAX query times before and after changes.

Sources [BTS field definitions](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ), [BTS reported causes](https://www.bts.gov/topics/airlines-and-airports/understanding-reporting-causes-flight-delays-and-cancellations).
