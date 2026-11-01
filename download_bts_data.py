#!/usr/bin/env python3
"""Download BTS Airline On-Time Performance CSVs, one file per month."""

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import shutil
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile, is_zipfile


BASE_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)


def month_range(start_year: int, start_month: int, end_year: int, end_month: int):
    for year in range(start_year, end_year + 1):
        first_month = start_month if year == start_year else 1
        last_month = end_month if year == end_year else 12
        for month in range(first_month, last_month + 1):
            yield year, month


def subtract_months(year: int, month: int, count: int) -> tuple[int, int]:
    month_index = year * 12 + month - 1 - count
    return month_index // 12, month_index % 12 + 1


def download_archive(year: int, month: int, destination: Path) -> bool:
    url = BASE_URL.format(year=year, month=month)
    request = Request(url, headers={"User-Agent": "BTS-Airline-Data-Downloader/1.0"})
    try:
        with urlopen(request, timeout=60) as response, destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    except HTTPError as error:
        if error.code == 404:
            return False
        raise RuntimeError(f"BTS returned HTTP {error.code} for {year}-{month:02d}.") from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to BTS: {error.reason}") from error

    if not is_zipfile(destination):
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"BTS did not return a valid ZIP file for {year}-{month:02d}.")
    return True


def extract_csv(archive_path: Path, output_path: Path, year: int, month: int) -> None:
    partial_path = output_path.with_suffix(output_path.suffix + ".part")
    try:
        with ZipFile(archive_path) as archive:
            csv_files = [
                item for item in archive.infolist()
                if not item.is_dir() and item.filename.lower().endswith(".csv")
            ]
            if len(csv_files) != 1:
                raise RuntimeError(
                    f"Expected one CSV in the BTS archive, found {len(csv_files)}."
                )
            with archive.open(csv_files[0]) as source, partial_path.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
        partial_path.replace(output_path)
    except BadZipFile as error:
        partial_path.unlink(missing_ok=True)
        raise RuntimeError(f"The BTS archive for {year}-{month:02d} is damaged.") from error
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise


def record_dataset_download(
    output_dir: Path,
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    available_months: list[tuple[int, int]],
    unavailable_months: list[tuple[int, int]],
    complete: bool,
) -> None:
    metadata_path = output_dir.parent / "dashboard_data.json"
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    download = payload.get("download")
    if not isinstance(download, dict):
        download = {}
    download.update({
        "last_download_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "requested_period_start": f"{start_year}-{start_month:02d}",
        "requested_period_end": f"{end_year}-{end_month:02d}",
        "requested_months": (end_year - start_year) * 12 + end_month - start_month + 1,
        "period_start": f"{available_months[0][0]}-{available_months[0][1]:02d}" if available_months else None,
        "period_end": f"{available_months[-1][0]}-{available_months[-1][1]:02d}" if available_months else None,
        "months_included": len(available_months),
        "unavailable_months": [
            f"{year}-{month:02d}" for year, month in unavailable_months
        ],
    })
    if complete:
        download["last_successful_pull"] = download["last_download_at"]
    payload["download"] = download
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=output_dir,
        prefix=".dashboard_data.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(payload, temporary, indent=2)
        temporary.write("\n")
    temporary_path.replace(metadata_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the most recent five years of BTS data, one CSV per month."
    )
    parser.add_argument("--year", type=int, help="Download one specific year; requires --month.")
    parser.add_argument("--month", type=int, choices=range(1, 13), help="Download one specific month; requires --year.")
    parser.add_argument(
        "--start-year",
        type=int,
        help="First year to download when fetching a custom range (starts in January).",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        help="Last year to download when fetching a custom range (default: current year).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Folder for downloaded monthly CSVs (default: ./data).",
    )
    args = parser.parse_args()

    if (args.year is None) != (args.month is None):
        parser.error("--year and --month must be provided together.")
    if args.year is not None and (args.start_year is not None or args.end_year is not None):
        parser.error("--year/--month cannot be combined with --start-year or --end-year.")
    if args.start_year is not None and args.start_year < 1987:
        parser.error("--start-year must be 1987 or later.")
    if (
        args.end_year is not None
        and args.start_year is not None
        and args.end_year < args.start_year
    ):
        parser.error("--end-year must be greater than or equal to --start-year.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "bts_month.zip"
        if args.year is not None:
            year, month = args.year, args.month
            if year < 1987 or not download_archive(year, month, archive_path):
                raise RuntimeError(f"No BTS monthly archive was found for {year}-{month:02d}.")
            output_path = args.output_dir / f"bts_on_time_{year}_{month:02d}.csv"
            if output_path.exists():
                print(f"Already exists; skipped {output_path}")
            else:
                extract_csv(archive_path, output_path, year, month)
                print(f"Downloaded {output_path}")
            record_dataset_download(
                args.output_dir,
                year,
                month,
                year,
                month,
                [(year, month)],
                [],
                True,
            )
            print("Downloaded 1 monthly CSV.")
            print("Source: https://transtats.bts.gov/")
            return

        current = date.today()
        end_year = min(args.end_year or current.year, current.year)
        end_month = current.month if end_year == current.year else 12
        if args.start_year is not None:
            start_year, start_month = args.start_year, 1
        elif args.end_year is not None:
            start_year, start_month = end_year - 4, 1
        else:
            start_year, start_month = subtract_months(end_year, end_month, 59)
        if start_year < 1987:
            raise RuntimeError("The requested range starts before BTS on-time data is available (1987).")
        if start_year > end_year:
            raise RuntimeError(
                f"Start year {start_year} is later than the current year {current.year}."
            )
        months = list(month_range(start_year, start_month, end_year, end_month))
        downloaded = 0
        skipped = 0
        missing_months = []

        for index, (year, month) in enumerate(months, 1):
            output_path = args.output_dir / f"bts_on_time_{year}_{month:02d}.csv"
            if output_path.exists():
                skipped += 1
                print(f"[{index}/{len(months)}] Already exists; skipped {output_path.name}")
                continue

            print(f"[{index}/{len(months)}] Downloading {year}-{month:02d}...", flush=True)
            if not download_archive(year, month, archive_path):
                missing_months.append((year, month))
                print(f"[{index}/{len(months)}] BTS has no archive for {year}-{month:02d}; skipped.")
                continue
            extract_csv(archive_path, output_path, year, month)
            downloaded += 1

    print(
        f"Finished: {downloaded} downloaded, {skipped} already present, "
        f"{len(missing_months)} unavailable month(s) from {start_year}-{start_month:02d} "
        f"through {end_year}-{end_month:02d}. Files are in {args.output_dir}."
    )
    available_months = [
        (year, month)
        for year, month in months
        if (args.output_dir / f"bts_on_time_{year}_{month:02d}.csv").is_file()
    ]
    complete = len(available_months) == len(months)
    record_dataset_download(
        args.output_dir,
        start_year,
        start_month,
        end_year,
        end_month,
        available_months,
        missing_months,
        complete,
    )
    print(
        f"Recorded this download time and the {len(available_months)} available months "
        f"from {available_months[0][0]}-{available_months[0][1]:02d} through "
        f"{available_months[-1][0]}-{available_months[-1][1]:02d}."
        if available_months else "Recorded this download time; no monthly files are available."
    )
    if not complete:
        print("The requested dataset is incomplete; keeping the previous successful download time.")
    else:
        print("Recorded the time the complete requested BTS dataset was downloaded.")
    print("Source: https://transtats.bts.gov/")


if __name__ == "__main__":
    main()
