Installation
============

PeriScope requires Python 3.11 or newer. CI tests Python 3.11–3.14 on Linux and
Python 3.11 on macOS. Install from a repository checkout:

.. code-block:: bash

   python3.11 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -e .
   periscope --help

Use another supported interpreter if appropriate. If upgrading an existing
Python 3.9 setup, create a fresh environment rather than reusing it. Use another
environment directory if you need to retain the old one.

For a non-editable installation, install a wheel produced by ``python -m build``:

.. code-block:: bash

   python -m pip install /path/to/periscope_planner-VERSION-py3-none-any.whl

Replace ``VERSION`` with the actual artifact version. Bundled target lists work
from any working directory in both editable and wheel installations. Help works
without contacting Horizons; an ordinary observing session requires network
access to JPL Horizons.

The ``test``, ``dev``, and ``docs`` extras install optional testing, development,
and documentation tools. There is no automated PyPI publishing in this repository.
