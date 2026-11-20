let
    Latest = fxLatest(stgFlights, "DOT_ID_Reporting_Airline", {"Reporting_Airline"}),
    Renamed = Table.RenameColumns(Latest, {{"DOT_ID_Reporting_Airline", "CarrierID"}, {"Reporting_Airline", "Code"}}),
    Label = Table.AddColumn(Renamed, "Carrier", each [Code] & " · " & Text.From([CarrierID], "en-US"), type text)
in
    Label
