# Airline On-Time Performance Dashboard

A lightweight dashboard for comparing airline on-time performance by airport route, built as a hands-on product management project with GitHub Copilot.

The project started with a practical question: **How can someone compare airline performance for the route they care about without getting lost in unrelated airport and airline data?** The result is a simple, locally run dashboard powered by U.S. Department of Transportation Bureau of Transportation Statistics (BTS) monthly data.

## Product decisions

- **One performance view:** airline, departure airport, arrival airport, completed flights, on-time performance, and rank in one table.
- **Route-aware airport filters:** choose a specific route or set one side to **All airports**. The table shows each matching airline-route result, and airport menus narrow to routes available under the other selection.
- **A more useful ranking:** airline-route results need at least **100 completed flights** to qualify. Eligible results are ranked by on-time performance; when rates tie, the result with more completed flights ranks higher. There is one overall Rank 1 for the current filters.
- **Clear data context:** display the BTS coverage period and download information so viewers can see which months are represented.

These choices reflect the product trade-offs explored during the build: focused comparisons, understandable rankings, and transparent limits on the data.

## Built with GitHub Copilot

I used GitHub Copilot as a coding partner to turn product requirements into a working, beginner-friendly application. The work included refining the user experience through feedback, shaping the data pipeline, implementing route filtering and ranking behavior, and validating the interface against the generated BTS dataset.

## Try it on Windows

1. Install Python 3.
2. Double-click **`run_dashboard.bat`**.
3. Wait for the available BTS files to download and the summary to build. The dashboard then opens in your browser at `http://127.0.0.1:8000`.

The initial download can take a while because BTS monthly files are large. An internet connection is needed to download data. Afterward, the downloaded files are reused, and the dashboard can be refreshed from local data.

### Run the steps manually

From PowerShell in the project folder:

```powershell
python download_bts_data.py
python build_airport_summary.py
python -m http.server 8000
```

Open [http://localhost:8000/index.html](http://localhost:8000/index.html). Keep the terminal open while using the dashboard, and press **Ctrl+C** to stop the server. A local server is required because the page loads `dashboard_data.json`.

## How to read the ranking

On-time performance is the percentage of completed flights that arrived less than 15 minutes late. Cancelled and diverted flights are excluded from completed-flight totals. Each row represents one airline on one airport pair, and only results with at least 100 completed flights are ranked. The Top 5, Top 10, and Top 100 options apply to the overall list for the current filters.

Airport choices and rankings use the monthly BTS CSV files available locally. BTS may not have published every requested month, so the latest month shown depends on data availability. The dashboard displays its actual coverage period; it should not be interpreted as a complete or official BTS ranking of every airline.

## Project files

| File | Purpose |
| --- | --- |
| `index.html` | Static dashboard UI and browser-side filtering, ranking, and sorting |
| `download_bts_data.py` | Downloads monthly BTS ZIP files and extracts the CSV data |
| `build_airport_summary.py` | Builds the combined dashboard JSON from local CSV files |
| `run_dashboard.bat` | Runs the download, summary build, and local web server on Windows |
| `dashboard_data.json` | Generated dashboard data; created locally and not tracked in Git |
| `data/` | Downloaded BTS monthly CSV files; kept out of Git because they are large |
| `USER_GUIDE.md` | Beginner-friendly operating instructions |

The dashboard uses plain HTML, CSS, and JavaScript. The Python scripts use the standard library; no database, backend, or extra Python packages are needed.

## Data source

[U.S. DOT BTS TranStats](https://transtats.bts.gov/) — Airline On-Time Performance data. Monthly downloads and generated summaries remain on the user's computer and are excluded from the repository.
