# PeriScope

PeriScope is an interactive observation-planning tool for minor planets. It
queries JPL Horizons for a target list, plots target elevation through a local
noon-to-noon observing window, and lets you filter the display by mean magnitude
and true anomaly. A linked RA/Dec view shows where the surviving targets are at a
selected ephemeris time.

## Setup

Create and activate a Python environment, then install the project in editable
mode from this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

PeriScope uses `astroquery` to call JPL Horizons, so the app needs a network
connection when it starts.

## Quick Start

Run the packaged command with a local observing date:

```bash
periscope --date 2026-01-01
```

By default, the command reads the bundled sample list at
`target_lists/aa_year1_paper.lst`, uses Apache Point Observatory / Horizons site
code `705`, samples the ephemerides every 15 minutes, and serves the Dash app at
`http://127.0.0.1:8050`. The bundled target lists are:

- `target_lists/aa_year1_paper.lst`
- `target_lists/MBC.lst`
- `target_lists/NEMBC.lst`

Use another target list by passing a text file with one object name per line:

```bash
periscope --objects target_lists/aa_year1_paper.lst --date 2026-01-01
periscope --objects target_lists/MBC.lst --date 2026-01-01
periscope --objects target_lists/NEMBC.lst --date 2026-01-01
```

If Horizons reports a short periodic-comet designation as ambiguous, PeriScope
retries with the newest matching Horizons record.

Other useful options:

```bash
periscope --site 304 --min-elevation 20 --step 10m --port 8051
periscope --help
```

## What the App Shows

The first plot shows elevation versus UTC time for every target that passes the
current filters. The magnitude slider keeps targets inside the selected mean
magnitude range. The true-anomaly slider excludes targets inside the selected
range, including ranges that wrap through 0 degrees.

The second plot shows RA/Dec for the filtered target set at the selected time.
Click a trace or marker to identify the corresponding target and its input-list
index.
