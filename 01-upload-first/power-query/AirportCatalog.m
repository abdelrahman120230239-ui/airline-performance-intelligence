let
    Roles = {"Origin", "Dest"},
    Seen = Table.Combine(List.Transform(Roles, (role) =>
        let
            Fields = {role & "AirportID", role, role & "CityName", role & "State"},
            Selected = Table.SelectColumns(stgFlights, {"FlightDate"} & Fields),
            Normalized = Table.RenameColumns(Selected, List.Zip({Fields, {"AirportID", "Code", "City", "State"}}))
        in
            Normalized
    )),
    Latest = fxLatest(Seen, "AirportID", {"Code", "City", "State"}),
    Label = Table.AddColumn(Latest, "Airport", each [Code] & " · " & Text.From([AirportID], "en-US"), type text)
in
    Label
