let
    Source = Table.SelectColumns(stgFlights, {
        "SourceRowID", "ReportMonth", "FlightDate", "DOT_ID_Reporting_Airline", "Flight_Number_Reporting_Airline",
        "OriginAirportID", "DestAirportID", "RouteID", "CRSDepTime", "CRSArrTime", "DepDelay", "ArrDelay",
        "Cancelled", "Diverted", "CancellationCode", "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"
    }),
    Renamed = Table.RenameColumns(Source, {
        {"DOT_ID_Reporting_Airline", "CarrierID"}, {"Flight_Number_Reporting_Airline", "FlightNumber"},
        {"DestAirportID", "DestinationAirportID"}, {"CRSDepTime", "ScheduledDepartureLocal"},
        {"CRSArrTime", "ScheduledArrivalLocal"}, {"DepDelay", "DepartureDelay"}, {"ArrDelay", "ArrivalDelay"}
    }),
    Reason = Table.AddColumn(Renamed, "CancellationKey", each
        if [Cancelled] = 0 then "-" else
        if List.Contains({"A", "B", "C", "D"}, [CancellationCode]) then [CancellationCode] else "?", type text),
    Arrival = Table.AddColumn(Reason, "ArrivalOutcome", each
        if [Cancelled] = 1 then "Cancelled" else if [Diverted] = 1 then "Diverted"
        else if [ArrivalDelay] = null then "Missing arrival delay"
        else if [ArrivalDelay] >= 15 then "Delayed 15+"
        else "On time", type text),
    Departure = Table.AddColumn(Arrival, "DepartureOutcome", each
        if [Cancelled] = 1 then "Cancelled" else if [DepartureDelay] = null then "Missing departure delay"
        else if [DepartureDelay] >= 15 then "Delayed 15+" else "On time", type text),
    Cause = Table.AddColumn(Departure, "HasReportedCause", each
        [ArrivalOutcome] = "Delayed 15+" and
        List.NonNullCount({[CarrierDelay], [WeatherDelay], [NASDelay], [SecurityDelay], [LateAircraftDelay]}) > 0, type logical),
    Result = Table.RemoveColumns(Cause, {"CancellationCode"})
in
    Result
