(source as table, key as text, attributes as list) as table =>
let
    Selected = Table.SelectColumns(source, {key, "FlightDate"} & attributes),
    Observations = Table.Distinct(Selected),
    SortFields = {{"FlightDate", Order.Descending}} & List.Transform(attributes, each {_, Order.Ascending}),
    Grouped = Table.Group(Observations, {key}, {{"Latest", each Table.Sort(_, SortFields){0}, type record}}),
    Expanded = Table.ExpandRecordColumn(Grouped, "Latest", attributes, attributes),
    Types = {{key, Int64.Type}} & List.Transform(attributes, each {_, type text}),
    Result = Table.TransformColumnTypes(Expanded, Types, "en-US")
in
    Result
