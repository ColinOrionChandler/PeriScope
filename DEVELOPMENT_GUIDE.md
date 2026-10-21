# PeriScope development guide

PeriScope is a CLI-launched Dash app for observing minor planets. Preserve the
noon-to-noon observing window, Horizons target resolution, magnitude and
true-anomaly filters, and linked plots when changing infrastructure. Tests must
use mocked Horizons responses and must not start a listening web server.

## Environment

Python 3.11 or newer is required. CI tests 3.11–3.14 on Linux and 3.11 on macOS.
Create a fresh environment when upgrading from the former Python 3.9 baseline:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
bash .setup_dev.sh
```

Use any supported interpreter in place of `python3.11`. Do not reuse a Python
3.9 environment. If `.venv` already exists, create a separate environment such as
`.venv-lincc` and activate that instead. The setup script installs the editable
package, developer and documentation dependencies, and local pre-commit hooks.

## Common commands

```bash
python -m pytest
ruff check src tests tools docs/conf.py
ruff format --check src tests tools docs/conf.py
pre-commit run --all-files
sphinx-build -W --keep-going -b html docs docs/build/html
python -m build
python tools/check_distribution.py dist
```

Use a clean `dist/` directory for each packaging check. The checker verifies
bundled resource bytes, installs the wheel in a temporary environment, and runs
the tests from outside the checkout. It also builds a wheel from the source
archive without Git metadata and repeats those checks. Dependency installation
needs network access; the tests themselves do not contact Horizons.

Ruff uses the LINCC rule set and 110-character lines. Run `ruff check --fix` and
`ruff format` to apply fixes, then inspect the diff. Test functions are exempt
from the public-function docstring rule. Generated version and API files are
excluded. The pytest hook fails on collection errors as well as test failures.

## Layout and compatibility

- `src/periscope/`: application package, generated `_version.py`, and `py.typed`.
- `src/periscope/target_lists/`: the single source of bundled `.lst` files.
- `tests/periscope/`: offline tests, including installation and startup contracts.
- `tools/check_distribution.py`: isolated artifact validation.
- `docs/`: Sphinx sources; generated pages and HTML are ignored.

The distribution is `periscope-planner`, the import is `periscope`, and the
repository is `ColinOrionChandler/PeriScope`. Keep these distinct in metadata and
workflows. Both `periscope` and `python -m periscope` use the same CLI.

Existing files passed to `--objects` take precedence. The three documented
`target_lists/*.lst` names also resolve to package resources from any directory.
Unknown relative paths and missing absolute paths remain errors. Do not edit the
bundled target lists as part of tooling maintenance.

## Versioning and builds

`setuptools-scm` generates `src/periscope/_version.py` from Git tags. Do not edit
or commit that file. `periscope.__version__` matches installed distribution
metadata. The existing `ac97dd8` commit is tagged `v0.1.0`; subsequent commits
produce development versions until a future release tag is deliberately created.

CI fetches complete history and tags. When publishing the migration branch for
review, push its existing `v0.1.0` baseline tag too. This is a Git version marker,
not a PyPI publication. Release tags and PyPI uploads require a separate release
workflow; this migration does not enable one. Use wheels or source distributions
built by `python -m build` when Git metadata is unavailable.

## Updating the LINCC template

This repository adopts LINCC Frameworks Python Project Template v2.3.1 using
Copier 9.1 or newer. `.copier-answers.yml` records the exact source, revision, and
choices. `project_name: PeriScope` preserves GitHub URLs; the package metadata is
intentionally customized to `periscope-planner`.

Start a clean update branch and run:

```bash
copier update --vcs-ref <reviewed-template-tag>
```

Review every change and resolve any `.rej` files before committing. Do not run
the template's new-project initialization script in this existing repository.
Retain these deliberate customizations:

- Distribution name, original runtime dependencies, `test` extra, CLI entry
  point, package resources, and Python 3.11 minimum.
- `docs` extra, no notebook/Jupyter dependency, and Ruff version matching the
  hook revision. Keep project dependencies in `pyproject.toml`.
- Existing application code and tests instead of template examples or a second
  generated CLI package.
- Full-history CI checkouts, the Linux/macOS matrix, artifact checks, and strict
  Sphinx builds. Keep coverage and docs previews as GitHub Actions artifacts.
- No PyPI publishing workflow, Codecov upload, pre-commit.ci writeback,
  benchmarks, external notifications, or scheduled smoke jobs.
- The tailored setup script, developer guide, and original README examples.

A same-version Copier update should be a no-op after merging customizations.
Run the full validation commands above after a real upgrade. The optional
Read the Docs configuration is prepared but no hosted project has been activated.
The project has no license file; selecting a license remains a separate decision.
