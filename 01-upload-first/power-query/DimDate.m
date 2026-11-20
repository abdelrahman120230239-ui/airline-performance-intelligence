let
    First = Date.StartOfYear(List.Min(SourceMonths)),
    Last = Date.EndOfYear(List.Max(SourceMonths)),
    Days = List.Dates(First, Duration.Days(Last - First) + 1, #duration(1, 0, 0, 0)),
    Dates = Table.FromColumns({Days}, type table [Date = date]),
    Years = Table.AddColumn(Dates, "Year", each Date.Year([Date]), Int64.Type),
    Months = Table.AddColumn(Years, "Year Month", each Date.ToText([Date], [Format="yyyy-MM", Culture="en-US"]), type text),
    MonthKey = Table.AddColumn(Months, "YearMonthKey", each [Year] * 100 + Date.Month([Date]), Int64.Type),
    Week = Table.AddColumn(MonthKey, "Weekday", each Date.DayOfWeekName([Date], "en-US"), type text),
    WeekSort = Table.AddColumn(Week, "WeekdayNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    Coverage = Table.AddColumn(WeekSort, "IsInScope", each List.Contains(SourceMonths, Date.StartOfMonth([Date])), type logical)
in
    Coverage
