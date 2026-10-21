Development
===========

Activate a supported Python environment and run:

.. code-block:: bash

   bash .setup_dev.sh
   python -m pytest
   pre-commit run --all-files
   sphinx-build -W --keep-going -b html docs docs/build/html
   python -m build
   python tools/check_distribution.py dist

Open ``docs/build/html/index.html`` to view the documentation. Use a clean
``dist/`` directory for packaging validation. Tests mock Horizons responses and
server startup. The distribution checker validates installed resources and runs
the suite outside the checkout against the wheel and a Git-free source rebuild.

Version metadata is derived from Git tags with ``setuptools-scm``. The generated
``src/periscope/_version.py`` must not be edited or committed. CI retrieves full
history and tags. Source distributions preserve their version without Git.

Template maintenance
--------------------

This project uses LINCC Frameworks Python Project Template v2.3.1. Copier's
answers are committed in ``.copier-answers.yml``. To update, use Copier 9.1+ on a
clean branch and select a reviewed template release:

.. code-block:: bash

   copier update --vcs-ref <reviewed-template-tag>

Review conflicts and retain the distribution name, CLI, bundled resources, and
workflow customizations. The repository's
`development guide <https://github.com/ColinOrionChandler/PeriScope/blob/main/DEVELOPMENT_GUIDE.md>`_
records the full update checklist. Do not run the template's new-project
initialization script in this existing repository.

CI saves coverage reports and HTML documentation as workflow artifacts. Read the
Docs configuration is prepared for future use; hosting, Codecov, and PyPI
publishing have not been activated. License selection is also deferred.
