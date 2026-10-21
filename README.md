# PeriScope

PeriScope is an interactive observation-planning tool for minor planets. It
queries JPL Horizons for a target list, plots target elevation through a local
noon-to-noon observing window, and lets you filter the display by mean magnitude
and true anomaly. A linked RA/Dec view shows where the surviving targets are at a
selected ephemeris time.

## Setup

Python 3.11 or newer is required. Create and activate a Python environment,
then install the project in editable mode from this repository:

```bash
python3.11 -m venv .venv
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
`http://127.0.0.1:8050`. These names resolve from any working directory.
The files are packaged in
`src/periscope/target_lists/`; an existing local file at the supplied path takes
precedence. The bundled target lists are:

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

## Development

For an older Python 3.9 installation, create a fresh environment with a supported
interpreter. You can use a different environment directory to retain the old one.

```bash
bash .setup_dev.sh
python -m pytest
pre-commit run --all-files
sphinx-build -W --keep-going -b html docs docs/build/html
```

Activate your environment before running the setup script. See
[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for packaging validation, CI, and
template update instructions. Open `docs/build/html/index.html` for the local
user guide and API reference. CI tests Python 3.11–3.14 on Linux and 3.11 on macOS.

PeriScope adopts the [LINCC Frameworks Python Project Template](https://github.com/lincc-frameworks/python-project-template)
v2.3.1 and records its configuration in `.copier-answers.yml` for future Copier
updates. Version metadata comes from Git tags through `setuptools-scm`. The
distribution name remains `periscope-planner`; use `import periscope` in Python.
