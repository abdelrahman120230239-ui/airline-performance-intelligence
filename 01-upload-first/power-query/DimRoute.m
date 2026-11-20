let
    Pairs = Table.Distinct(Table.SelectColumns(stgFlights, {"RouteID", "OriginAirportID", "DestAirportID"})),
    Airports = Table.Buffer(Table.SelectColumns(AirportCatalog, {"AirportID", "Airport"})),
    OriginJoin = Table.NestedJoin(Pairs, "OriginAirportID", Airports, "AirportID", "O", JoinKind.LeftOuter),
    Origin = Table.ExpandTableColumn(OriginJoin, "O", {"Airport"}, {"Origin"}),
    DestJoin = Table.NestedJoin(Origin, "DestAirportID", Airports, "AirportID", "D", JoinKind.LeftOuter),
    Dest = Table.ExpandTableColumn(DestJoin, "D", {"Airport"}, {"Destination"}),
    Label = Table.AddColumn(Dest, "Route", each [Origin] & " → " & [Destination], type text),
    Result = Table.SelectColumns(Label, {"RouteID", "Route"})
in
    Result
