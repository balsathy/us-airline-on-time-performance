#!/usr/bin/env python3
"""Build airline and airport BTS on-time summaries from downloaded monthly CSV files."""

import argparse
import csv
import json
from pathlib import Path
import re
import tempfile


MONTH_FILE = re.compile(r"bts_on_time_(\d{4})_(\d{2})\.csv$")
REQUIRED_FIELDS = {
    "Origin",
    "Dest",
    "Reporting_Airline",
    "DepDel15",
    "ArrDel15",
    "Cancelled",
    "Diverted",
    "Flights",
}

AIRLINE_NAMES = {
    "9E": "Endeavor Air",
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "F9": "Frontier Airlines",
    "G4": "Allegiant Air",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air",
    "NK": "Spirit Airlines",
    "OH": "PSA Airlines",
    "OO": "SkyWest Airlines",
    "QX": "Horizon Air",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "YV": "Mesa Airlines",
    "YX": "Republic Airways",
    "ZW": "Air Wisconsin",
}
def number(row: dict[str, str], field: str) -> float | None:
    try:
        return float(row[field])
    except (TypeError, ValueError, KeyError):
        return None


def add_flight(
    airports: dict[tuple[str, str], dict[str, float | str]],
    role: str,
    code: str,
    city: str,
    flights: float,
    on_time: bool,
) -> None:
    record = airports.setdefault(
        (role, code),
        {"airport": code, "city": city, "flights": 0, "on_time": 0},
    )
    record["flights"] = float(record["flights"]) + flights
    if on_time:
        record["on_time"] = float(record["on_time"]) + flights


def add_airline_flight(
    summary: dict[tuple[str, str, str, str], list[float]],
    scope: str,
    origin: str,
    destination: str,
    carrier: str,
    flights: float,
    arrival_on_time: bool,
) -> None:
    record = summary.setdefault((scope, origin, destination, carrier), [0, 0])
    record[0] += flights
    if arrival_on_time:
        record[1] += flights


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the combined airline and airport dashboard data from BTS files."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data"),
        help="Folder containing bts_on_time_YYYY_MM.csv files (default: ./data).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dashboard_data.json"),
        help="Combined dashboard data output (default: ./dashboard_data.json).",
    )
    args = parser.parse_args()

    files = sorted(
        (path for path in args.input_dir.glob("bts_on_time_*.csv") if MONTH_FILE.fullmatch(path.name)),
        key=lambda path: tuple(map(int, MONTH_FILE.fullmatch(path.name).groups())),
    )
    if not files:
        raise SystemExit(
            f"No BTS monthly CSV files found in {args.input_dir}. "
            "Run download_bts_data.py first."
        )

    airports: dict[tuple[str, str], dict[str, float | str]] = {}
    airline_totals: dict[tuple[str, str, str, str], list[float]] = {}
    processed_rows = 0
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            fields = set(reader.fieldnames or [])
            missing_fields = REQUIRED_FIELDS - fields
            if missing_fields:
                raise SystemExit(
                    f"{path} is missing BTS fields: {', '.join(sorted(missing_fields))}"
                )

            for row in reader:
                if number(row, "Cancelled") != 0 or number(row, "Diverted") != 0:
                    continue
                flights = number(row, "Flights")
                departure_on_time = number(row, "DepDel15")
                arrival_on_time = number(row, "ArrDel15")
                if flights is None or flights <= 0:
                    continue
                origin_code = (row.get("Origin") or "").strip()
                destination_code = (row.get("Dest") or "").strip()
                carrier = (row.get("Reporting_Airline") or "").strip()

                if carrier and origin_code and destination_code:
                    arrival_is_on_time = arrival_on_time == 0
                    add_airline_flight(
                        airline_totals,
                        "all",
                        "",
                        "",
                        carrier,
                        flights,
                        arrival_is_on_time,
                    )
                    add_airline_flight(
                        airline_totals,
                        "departure",
                        origin_code,
                        "",
                        carrier,
                        flights,
                        arrival_is_on_time,
                    )
                    add_airline_flight(
                        airline_totals,
                        "arrival",
                        "",
                        destination_code,
                        carrier,
                        flights,
                        arrival_is_on_time,
                    )
                    add_airline_flight(
                        airline_totals,
                        "route",
                        origin_code,
                        destination_code,
                        carrier,
                        flights,
                        arrival_is_on_time,
                    )

                if departure_on_time is not None:
                    if origin_code:
                        add_flight(
                            airports,
                            "origin",
                            origin_code,
                            (row.get("OriginCityName") or "").strip(),
                            flights,
                            departure_on_time == 0,
                        )
                if arrival_on_time is not None:
                    if destination_code:
                        add_flight(
                            airports,
                            "destination",
                            destination_code,
                            (row.get("DestCityName") or "").strip(),
                            flights,
                            arrival_on_time == 0,
                        )
                processed_rows += 1

    if not airports:
        raise SystemExit("No completed airport records with on-time data were found.")

    months = [tuple(map(int, MONTH_FILE.fullmatch(path.name).groups())) for path in files]
    start_year, start_month = months[0]
    end_year, end_month = months[-1]
    download_metadata = {}
    if args.output.exists():
        try:
            previous_data = json.loads(args.output.read_text(encoding="utf-8"))
            download_metadata = previous_data.get("download", {})
        except (OSError, json.JSONDecodeError):
            download_metadata = {}
    if not download_metadata:
        try:
            download_metadata = json.loads(
                (args.input_dir / "bts_refresh.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            download_metadata = {}

    records = []
    for (role, _), airport in airports.items():
        flights = int(airport["flights"])
        on_time = int(airport["on_time"])
        records.append(
            {
                "role": role,
                "airport": airport["airport"],
                "city": airport["city"],
                "flights": flights,
                "on_time": round(on_time / flights * 100, 2),
            }
        )

    airline_records = []
    for (scope, origin, destination, carrier), (flights, on_time_flights) in airline_totals.items():
        airline_records.append(
            {
                "scope": scope,
                "departure": origin,
                "arrival": destination,
                "carrier": carrier,
                "airline": AIRLINE_NAMES.get(carrier, carrier),
                "flights": int(flights),
                "on_time": round(on_time_flights / flights * 100, 2),
            }
        )

    payload = {
        "source": "U.S. DOT Bureau of Transportation Statistics (BTS) TranStats",
        "coverage": {
            "period_start": f"{start_year}-{start_month:02d}",
            "period_end": f"{end_year}-{end_month:02d}",
            "months_included": len(months),
        },
        "download": download_metadata,
        "processed_flights": processed_rows,
        "airports": sorted(records, key=lambda row: (row["role"], row["airport"])),
        "airlines": sorted(
            airline_records,
            key=lambda row: (row["scope"], row["departure"], row["arrival"], row["carrier"]),
        ),
    }

    def write_json_atomically(path: Path, document: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(document, temporary, indent=2)
            temporary.write("\n")
        temporary_path.replace(path)

    write_json_atomically(args.output, payload)

    print(
        f"Created {args.output} for {payload['coverage']['period_start']} through "
        f"{payload['coverage']['period_end']} ({len(months)} monthly files, "
        f"{len(records):,} airport/role records and {len(airline_records):,} airline records)."
    )
    print(f"Processed {processed_rows:,} completed flight rows.")
    if len(months) < 60:
        print(
            f"Note: results include {len(months)} available monthly "
            "files from the downloaded BTS data."
        )


if __name__ == "__main__":
    main()
