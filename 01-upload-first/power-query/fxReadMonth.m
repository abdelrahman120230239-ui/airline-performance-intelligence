(month as date) as table =>
let
    MonthLabel = Date.ToText(month, [Format="yyyy-MM", Culture="en-US"]),
    MonthNumber = Date.Year(month) * 100 + Date.Month(month),
    Path = Text.TrimEnd(pRawFolder, {"\", "/"}) & "\" & MonthLabel & ".csv",
    Raw = Csv.Document(File.Contents(Path), [Delimiter=",", Encoding=1252, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true, Culture="en-US"]),
    TextColumns = {
        "Reporting_Airline", "Flight_Number_Reporting_Airline", "Origin", "OriginCityName",
        "OriginState", "Dest", "DestCityName", "DestState", "CRSDepTime", "CRSArrTime", "CancellationCode"
    },
    NumberColumns = {
        "DOT_ID_Reporting_Airline", "OriginAirportID", "DestAirportID", "DepDelay", "ArrDelay",
        "Cancelled", "Diverted", "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay",
        "LateAircraftDelay", "Flights"
    },
    Selected = Table.SelectColumns(Headers, {"FlightDate"} & TextColumns & NumberColumns),
    Typed = Table.TransformColumns(
        Selected,
        {{"FlightDate", each Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"]), type date}} &
        List.Transform(TextColumns, (name) => {name,
            each if _ = null or Text.Trim(_) = "" then null else Text.Trim(_), type nullable text}) &
        List.Transform(NumberColumns, (name) => {name,
            each if _ = null or _ = "" then null else
                let n = Number.FromText(_, "en-US")
                in if n = Number.RoundDown(n) then Int64.From(n)
                   else error Error.Record("BTS contract", "Expected a whole number", [Field=name, Value=_]),
            Int64.Type})
    ),
    Indexed = Table.AddIndexColumn(Typed, "_Ordinal", 1, 1, Int64.Type),
    Traced = Table.AddColumn(Indexed, "SourceRowID", each
        if [FlightDate] = null or Date.StartOfMonth([FlightDate]) <> month or
            [Flights] <> 1 or not List.Contains({0, 1}, [Cancelled]) or not List.Contains({0, 1}, [Diverted]) or
            ([Cancelled] = 1 and [Diverted] = 1) or [DOT_ID_Reporting_Airline] = null or
            [DOT_ID_Reporting_Airline] <= 0 or [OriginAirportID] = null or [DestAirportID] = null or
            [OriginAirportID] < 1 or [OriginAirportID] > 999999 or [DestAirportID] < 1 or
            [DestAirportID] > 999999 or [_Ordinal] >= 10000000 or
            [Reporting_Airline] = null or [Origin] = null or [Dest] = null or
            [Flight_Number_Reporting_Airline] = null or [CRSDepTime] = null
        then error Error.Record("BTS contract", "Unexpected month, key, flight count or flags", [Month=MonthLabel, CsvDataRow=[_Ordinal]])
        else MonthNumber * 10000000 + [_Ordinal], Int64.Type),
    MonthTagged = Table.AddColumn(Traced, "ReportMonth", each MonthLabel, type text),
    Result = Table.RemoveColumns(MonthTagged, {"_Ordinal", "Flights"})
in
    Result
