let
    CheckedMonths = if List.Count(SourceMonths) = 0 or List.Count(List.Distinct(SourceMonths)) <> List.Count(SourceMonths) or
        not List.AllTrue(List.Transform(SourceMonths, each Date.StartOfMonth(_) = _))
        then error "SourceMonths must contain distinct month starts" else SourceMonths,
    Appended = Table.Combine(List.Transform(CheckedMonths, each fxReadMonth(_))),
    Route = Table.AddColumn(Appended, "RouteID", each [OriginAirportID] * 1000000 + [DestAirportID], Int64.Type)
in
    Route
