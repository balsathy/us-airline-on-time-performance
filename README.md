# Airline on-time performance

A small, static airline comparison page built with plain HTML, CSS, and JavaScript.

For a beginner-friendly explanation of the files and run order, see [USER_GUIDE.md](USER_GUIDE.md).

The dashboard uses locally downloaded BTS monthly files to build airline route results and airport dropdown choices from the same coverage period.

## Quick start

On Windows, double-click `run_dashboard.bat`. It downloads any available files in the rolling 60-month BTS window, rebuilds `dashboard_data.json`, starts the local dashboard server, and opens the page in your browser. The first run may take a while because BTS monthly files are large. Python 3 and an internet connection are required for the initial download.

To run steps manually, open a terminal in this folder and start a local web server:

```powershell
python -m http.server 8000
```

Then visit `http://localhost:8000` in your browser. The browser must use a local server to load `dashboard_data.json`; opening `index.html` directly as a file will not load it.

The dashboard has one airline performance table with rank, airline, departure airport, arrival airport, completed flights, and on-time performance columns. A single **Filters** section groups airline search and airport options. Only airline-route results with at least 100 completed flights are ranked, preventing a one-flight 100% rate from leading the ranking; results below 100 are excluded and noted above the table. Airport dropdowns list only airports connected by available routes under the other selected filter, with the BTS city/market name shown beside each code. To see performance for a specific route, select one departure airport and one arrival airport; the same airport cannot be used for both. Setting one side to **All airports** shows each matching route separately and aggregates each airline's results within that route. Airlines are ranked in one overall list for the current filters, so there is exactly one Rank 1; when on-time rates tie, the airline with more completed flights ranks higher. When all airports are shown, Top 5/10/100 limits apply to the overall list, not each route. Completed flights exclude cancellations and diversions.

Airline route summaries and airport dropdown choices are generated from the same available monthly BTS files. No packages, backend, or external runtime data services are required.

## Download BTS source data

Run the downloader to save a rolling 60-month window ending with the current month, one CSV per month:

```powershell
python download_bts_data.py
```

The downloader includes the current calendar month in the requested range. BTS may not have published that month's archive yet; unavailable months are reported and skipped. It skips CSVs already downloaded, so you can rerun it to resume or refresh the range. To download a specific month instead, for example December 2025:

```powershell
python download_bts_data.py --year 2025 --month 12
```

To choose a custom year range, use `--start-year` and optionally `--end-year`; for example:

```powershell
python download_bts_data.py --start-year 2021 --end-year 2025
```

The CSVs are saved under `data/` by default. Change the destination with `--output-dir`. The script uses Python's standard library and BTS's monthly ZIP downloads. Download time, requested range, and unavailable months are saved in the `download` section of `dashboard_data.json`.

After downloading the monthly files, build the dashboard data:

```powershell
python build_airport_summary.py
```

This creates or refreshes one file, `dashboard_data.json`, containing shared coverage, download metadata, airport dropdown options, and airline records for airport, route, and airport-filtered scopes. The performance table ranks each airline-route result by on-time performance in one overall list for the selected filters. Rerun the downloader and summary builder to refresh data; only the summary builder is needed to refresh results from files already downloaded.
