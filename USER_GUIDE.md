# User Guide

This project is a small local dashboard for comparing airlines' on-time performance on a selected departure-arrival airport route. It uses BTS monthly files saved on your computer; it does not need a database, backend service, or extra Python packages.

## What the files do

| File or folder | What it contains |
| --- | --- |
| `index.html` | The dashboard page, including its filters, single combined performance table, and browser-side code. |
| `download_bts_data.py` | Downloads monthly BTS on-time-performance CSV files into `data/`. Existing monthly files are skipped so a later run can continue or refresh the collection. |
| `build_airport_summary.py` | Reads the downloaded CSV files and builds one combined JSON file for the dashboard. |
| `run_dashboard.bat` | On Windows, downloads available BTS files, rebuilds the dashboard data, starts the local server, and opens the page. |
| `dashboard_data.json` | The single generated JSON file used by the dashboard. It contains shared coverage, download metadata, airport dropdown choices, and airline route results. |
| `data/bts_on_time_YYYY_MM.csv` | A downloaded BTS source file for one month. These are the raw monthly inputs used to build the summaries. |
| `README.md` | Project overview and reference instructions for the scripts and dashboard. |
| `USER_GUIDE.md` | This plain-language guide to the files and the steps to run the project. |

The summary builder uses every valid monthly BTS CSV currently in `data\` for airline route results and airport dropdown choices. They share one coverage period. If the first available CSV is November 2021, the displayed range begins then; missing earlier files are not treated as data.

## Run the project from scratch

On Windows, double-click `run_dashboard.bat` to download available data, build the summary, start the local server, and open the dashboard. This requires Python 3 and an internet connection for downloading; the first download and summary build can take a while.

To run the steps manually, open PowerShell in the project folder and follow these steps:

1. **Download the BTS monthly data** (requires an internet connection):

   ```powershell
   python download_bts_data.py
   ```

   The script saves monthly CSV files under `data\` and writes download metadata into `dashboard_data.json`. BTS may not have published every requested month yet. The script reports unavailable months and skips files that are already present.

2. **Build the dashboard summaries** from the CSV files:

   ```powershell
   python build_airport_summary.py
   ```

   This creates or refreshes the single `dashboard_data.json` file in the project folder. It holds airline route results, airport dropdown choices, and their shared coverage.

3. **Start a local web server** in the project folder:

   ```powershell
   python -m http.server 8000
   ```

4. **Open the dashboard** in a browser at:

   ```text
   http://localhost:8000/index.html
   ```

Keep the PowerShell window running while using the dashboard. To stop the server, press **Ctrl+C** in that window.

## Refresh results without downloading again

If the needed CSV files are already in `data\`, skip the download step and run:

```powershell
python build_airport_summary.py
```

Then reload the dashboard page in the browser. The browser only needs the local server; it does not execute the Python scripts.

## What to check on the page

- Select one departure airport and one arrival airport to see each airline's completed-flight count and on-time performance on that specific route. Airlines are ranked by on-time performance in one overall list for the current filters; if rates tie, the airline with more completed flights ranks higher.
- An airline-route must have at least 100 completed flights to be ranked. This avoids giving a one-flight route the lead just because its on-time rate is 100%. The results summary states this minimum and counts any excluded route results.
- The last BTS dataset download time and unavailable months are stored in the `download` section of `dashboard_data.json`.
- An **All airports** selection broadens one side of the airport filter, while the other side remains one airport. Each matching departure-arrival pair is shown separately, and each airline is aggregated within that route. All displayed airline-route results share one overall ranking, so only one row has Rank 1. Top 5/10/100 limits apply to the overall list.
- The same airport cannot be selected as both departure and arrival; choosing a duplicate automatically sets the other filter to **All airports**.
- Airport dropdowns list only airports connected to the other selected airport through available routes. Each option shows the airport code with its BTS city/market name.
- Airline on-time performance is the share of completed flights that arrived less than 15 minutes late. Cancelled and diverted flights are excluded from completed-flight totals.
