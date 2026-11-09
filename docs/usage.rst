Using PeriScope
===============

Start an observing session with a date in the selected observatory's local time:

.. code-block:: bash

   periscope --date 2026-01-01
   python -m periscope --date 2026-01-01

The default site is Apache Point Observatory (Horizons code ``705``), the sample
interval is 15 minutes, and the server listens at ``http://127.0.0.1:8050``.
The observing window runs from local noon on the selected date to local noon the
following day; the elevation plot displays UTC times. Omit ``--date`` to use the
current local date at the site.

Target lists
------------

These bundled-list names work from any directory:

.. code-block:: bash

   periscope --objects target_lists/aa_year1_paper.lst --date 2026-01-01
   periscope --objects target_lists/MBC.lst --date 2026-01-01
   periscope --objects target_lists/NEMBC.lst --date 2026-01-01

The first list is the default. The files live inside the installed package,
under ``periscope/target_lists/``. An existing local file at the supplied path
takes precedence over the bundled alias. Custom files contain one target name
per line; blank lines are ignored:

.. code-block:: bash

   periscope --objects /path/to/my-targets.lst --date 2026-01-01

Missing custom paths and empty files produce a CLI error. A missing absolute
path is never replaced with a bundled list. If Horizons reports a short periodic
comet designation as ambiguous, PeriScope retries using the newest matching
record from Horizons' response.

Options and plots
-----------------

.. code-block:: bash

   periscope --site 304 --min-elevation 20 --step 10m --port 8051
   periscope --help

Use ``--help`` for supported sites and all options, including ``--host``,
``--debug``, and ``--title``.

The magnitude slider retains targets inside the selected mean-magnitude range.
The true-anomaly slider excludes targets inside the selected range, including
ranges that wrap through zero degrees. The time slider selects the ephemeris
sample shown in the linked RA/Dec plot. Click a trace or marker to identify its
target and input-list index. Slider interactions reuse the fetched ephemerides.
