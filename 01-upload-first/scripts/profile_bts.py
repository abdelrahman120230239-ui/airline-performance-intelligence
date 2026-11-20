"""Independently profile and reconcile downloaded BTS Reporting Carrier CSVs."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

SOURCE = [
    "FlightDate", "DOT_ID_Reporting_Airline", "Reporting_Airline",
    "Flight_Number_Reporting_Airline", "OriginAirportID", "Origin", "OriginCityName",
    "OriginState", "DestAirportID", "Dest", "DestCityName", "DestState", "CRSDepTime",
    "CRSArrTime", "DepDelay", "DepDel15", "ArrDelay", "ArrDel15", "Cancelled",
    "CancellationCode", "Diverted", "CarrierDelay", "WeatherDelay", "NASDelay",
    "SecurityDelay", "LateAircraftDelay", "Flights",
]
TYPES = {field: "string" for field in SOURCE[:14] + ["CancellationCode"]}
CAUSES = SOURCE[21:26]
METRICS = ["scheduled", "completed", "departed", "dep_eligible", "dep_ontime", "arr_eligible",
           "ontime", "late", "cancelled", "diverted", "late60", "late_minutes",
           "cause_covered", *CAUSES]
KEY = ["FlightDate", "DOT_ID_Reporting_Airline", "Flight_Number_Reporting_Airline",
       "OriginAirportID", "DestAirportID", "CRSDepTime"]

def aggregate(frame, fields, destination):
    for group, row in frame.groupby(fields, sort=True)[METRICS].sum().iterrows():
        key = "|".join(group) if isinstance(group, tuple) else group
        destination.setdefault(str(key), Counter()).update({k: int(v) for k, v in row.items()})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    summaries = {}
    groups = defaultdict(dict)
    airports = {}
    fixture = []
    boundary = []
    for path in sorted(args.raw.glob("20??-??.csv")):
        df = pd.read_csv(path, usecols=SOURCE, dtype=TYPES, encoding="cp1252", keep_default_na=False, na_values=[""])
        c, v, a, d = df.Cancelled.eq(1), df.Diverted.eq(1), df.ArrDelay, df.DepDelay
        complete = df.Cancelled.eq(0) & df.Diverted.eq(0)
        eligible = complete & a.notna()
        dep_eligible = df.Cancelled.eq(0) & d.notna()
        late = eligible & a.ge(15)
        cause_valid = df[CAUSES].notna().all(axis=1) & df[CAUSES].ge(0).all(axis=1)
        matched = df[CAUSES].sum(axis=1).eq(a)
        assert df.FlightDate.str.startswith(path.stem).all()
        assert df.Flights.eq(1).all() and not (c & v).any()
        assert not df[KEY].isna().any().any()
        assert df[["Cancelled", "Diverted"]].isin([0, 1]).all().all()
        for prefix in ("Origin", "Dest"):
            airports.update(dict(zip(df[prefix+"AirportID"], df[prefix])))
        summaries[path.stem] = {
            "rows": len(df), "date_min": df.FlightDate.min(), "date_max": df.FlightDate.max(),
            "nulls": {k:int(v) for k,v in df[SOURCE].isna().sum().items()},
            "diagnostics": {
                "duplicate_candidate_excess": int(df.duplicated(subset=KEY).sum()),
                "duplicate_projected_row_excess": int(df.duplicated(subset=SOURCE).sum()),
                "completed_without_arrival_delay": int((complete & a.isna()).sum()),
                "noncancelled_without_departure_delay": int((df.Cancelled.eq(0) & d.isna()).sum()),
                "cancel_with_unknown_reason": int((c & ~df.CancellationCode.isin(list("ABCD"))).sum()),
                "cancel_code_for_noncancelled": int((~c & df.CancellationCode.notna()).sum()),
                "arrival_indicator_disagreement": int((eligible & (df.ArrDel15.isna() | df.ArrDel15.ne(a.ge(15)))).sum()),
                "departure_indicator_disagreement": int((dep_eligible & (df.DepDel15.isna() | df.DepDel15.ne(d.ge(15)))).sum()),
                "late_missing_all_causes": int((late & df[CAUSES].isna().all(axis=1)).sum()),
                "late_incomplete_causes": int((late & ~cause_valid).sum()),
                "late_cause_sum_disagreement": int((late & cause_valid & ~matched).sum()),
                "nonlate_with_any_cause": int((~late & df[CAUSES].notna().any(axis=1)).sum()),
            },
        }
        if path.stem == "2025-01":
            for selector in [eligible & a.eq(14), eligible & a.eq(15), c, v]:
                record = df.loc[selector, ["FlightDate","Reporting_Airline","Origin","Dest","ArrDelay","Cancelled","Diverted"]].head(1)
                record = record.assign(SourceRowID=(202501*10_000_000 + record.index + 1))
                boundary.extend(json.loads(record.to_json(orient="records")))
        candidate=df[df.FlightDate.eq("2025-01-01") & df.Reporting_Airline.eq("AA")
                     & df.Origin.eq("JFK") & df.Dest.eq("LAX")].sort_values("CRSDepTime")
        fixture.extend(json.loads(candidate.assign(SourceRowID=(int(path.stem.replace("-", ""))*10_000_000 + candidate.index + 1))
            [["SourceRowID", "FlightDate", "Flight_Number_Reporting_Airline", "CRSDepTime",
              "Cancelled", "Diverted", "ArrDelay", *CAUSES]].to_json(orient="records")))
        frame = pd.DataFrame({
            "month":path.stem, "year":path.stem[:4], "date":df.FlightDate, "carrier":df.Reporting_Airline,
            "carrier_id":df.DOT_ID_Reporting_Airline, "origin":df.Origin, "destination":df.Dest,
            "route":df.Origin + " → " + df.Dest, "reason":df.CancellationCode.where(c & df.CancellationCode.isin(list("ABCD")), "?"),
            "scheduled":1, "completed":complete, "departed":df.Cancelled.eq(0),
            "dep_eligible":dep_eligible, "dep_ontime":dep_eligible & d.lt(15),
            "arr_eligible":eligible, "ontime":eligible & a.lt(15), "late":late,
            "cancelled":c, "diverted":v, "late60":eligible & a.ge(60),
            "late_minutes":a.where(late, 0), "cause_covered":late & df[CAUSES].notna().any(axis=1),
        })
        for cause in CAUSES:
            frame[cause] = df[cause].where(late, 0).fillna(0)
        for key in ("month","year","date","carrier","carrier_id","origin","destination","route"):
            aggregate(frame,key,groups[key])
            if key in ("carrier","carrier_id","origin","destination","route"):
                aggregate(frame,["year",key],groups[key+"_year"])
        aggregate(frame[c], "reason", groups["cancellation_reason"])
        aggregate(frame[c], ["year","reason"], groups["cancellation_reason_year"])
        print(path.name, len(df), flush=True)
    args.output.write_text(json.dumps({"profile":summaries, "aggregates":groups, "fixture":fixture,
                                       "boundary":boundary, "airport_count":len(airports)}, indent=2),encoding="utf-8")

if __name__ == "__main__":
    main()
