# 3. Report implementation and access

## Four connected pages

| Page | Visuals and actions |
|---|---|
| Executive Overview | Scheduled volume, arrival OTP, cancellations, diversions and matched-date YoY. Select a monthly bar or hover for the reliability tooltip. Use the scorecard to read exact monthly values. |
| Airline Benchmarking | Carrier OTP and a scorecard with comparable volume, cancellation rate, weighted network gap and dynamic rank. Use the carrier slicer to choose a peer set. Hover over a carrier to see its denominators and outcomes. |
| Airport and Route Analysis | Independent origin and destination charts, sorted by late-arrival minutes, and a directional route table. Select a route and click Open flight records, or right-click its row and choose Drill through > Flight Records. |
| Delay and Cancellation Investigation | Disruption KPIs, five reported delay-minute buckets, and cancellation counts by reported reason. Chart and Table bookmarks switch attribution views while keeping slicer selections. |

The navigation buttons and four synchronized slicers (reporting month, reporting carrier, scheduled origin, scheduled destination) are included in PBIR. A locked report-level coverage filter restricts the date picker to the four observed months. Native Desktop Edit mode may require Ctrl+click for action buttons.

## Inspect or recreate the interactions

1. In View > Sync slicers, confirm that all four slicers are visible and synced across the four main pages. Pick January and February 2025 on Executive Overview and navigate to Airports & routes to verify the selection stays active.
2. On the hidden Flight Records page, confirm that DimRoute[Route] is the drill-through field and Keep all filters is on. On Airports & routes, select a table row and Ctrl+click Open flight records. Check the heading, dates, and carrier values, then use Back.
3. Open the hidden Reliability Tooltip page in edit mode. Under Page information confirm use as tooltip. On the executive monthly chart, carrier chart and airport charts inspect Format > General > Tooltips and confirm the report-page tooltip selects Reliability Tooltip. Hover and compare comparable arrivals with the scorecard or a DAX query.
4. In View > Selection and Bookmarks, inspect the two investigation states. Chart shows the cause bars, Table shows the cause rows. The bookmark settings capture Display and preserve Data. Pick a single carrier, toggle both ways and verify the population stays fixed.
5. In Format > General > Title use the fx field-value binding to inspect the trend, benchmark, route, disruption, and drill-through titles. Multiple selected months appear in chronological order.
6. Use Edit interactions to confirm that selecting a route or chart point passes expected context without replacing the independent slicers. Rerun the reconciliation if you change relationships or interactions.

## Carrier-level sample RLS

CarrierViewer restricts DimCarrier by a lower-cased USERPRINCIPALNAME() lookup in CarrierAccess. The same role filters the hidden mapping table to the connected UPN. A principal with no mapped carrier returns zero accessible rows. Active, single-direction DimCarrier → FactFlight propagates the restriction to all flight visuals and measures. ALL and ALLSELECTED cannot remove RLS. A carrier-restricted user sees a weighted benchmark for their permitted population. Public airport and route labels can still appear in dimension slicers.

| Fictitious UPN | Carrier entitlement | Jan–Feb 2025 scheduled flights |
|---|---|---:|
| ops.aa@example.com | AA (19805) | 144,964 |
| ops.network@example.com | AA and DL (19805, 19790) | 292,603 |
| unmapped@example.com | No carrier | 0 |

In Desktop use Modeling > Manage roles to inspect CarrierViewer. Use Modeling > View as and select both CarrierViewer and Other user. Enter each sample UPN and select January and February 2025. Check KPI counts, the list of visible carriers, drill-through, and the weighted benchmark. Clear the role and verify that 1,044,631 scheduled flights return. When publishing privately, replace the sample UPNs with governed identities, assign the role in the semantic model's Security settings, and test with service Viewer users. Workspace Admin, Member and Contributor permissions bypass RLS. Leave the portfolio local unless publishing is independently authorized.

## Performance and usability

- Keep the model in Import mode for the four-month sample. Use role-appropriate slicers and measures, and leave technical keys hidden except for trace IDs on drill-through.
- The report limits airport charts to six stations per role and the route table to fifteen routes by delay minutes. Route rank requires 500 comparable arrivals and respects the visual peer context. Carrier rank uses 1,000. Compare these cutoffs against the operational population when adapting the report.
- Use Performance Analyzer after a full refresh. Record a cold open and warm repeats for period changes, a carrier benchmark, an airport intersection, and drill-through. Copy slow queries to DAX Query View and inspect storage- and formula-engine work with DAX Studio if installed. Large route histories benefit from a precomputed route-date aggregate while the detail fact remains available for drill-through.
- Test title wrapping, filter-clear behavior, keyboard traversal, chart legends and rate formatting in View mode. Capture the four main pages after verification.

Sources [Microsoft drill-through](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-drillthrough), [Report-page tooltips](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-tooltips), [Desktop bookmarks](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-bookmarks), [RLS](https://learn.microsoft.com/en-us/fabric/security/service-admin-row-level-security), [Performance Analyzer](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-performance-analyzer).
