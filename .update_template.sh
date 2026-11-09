#!/usr/bin/env bash
# Preserve intentional omissions when updating the upstream LINCC template.
set -euo pipefail
cd "$(dirname "$0")"
revision="${1:?Usage: bash .update_template.sh <reviewed-template-tag> [copier options]}"
shift
exec copier update --vcs-ref "$revision" --skip-tasks \
  --exclude .initialize_new_project.sh \
  --exclude requirements.txt \
  --exclude docs/requirements.txt \
  --exclude docs/notebooks \
  --exclude docs/pre_executed \
  --exclude .github/ISSUE_TEMPLATE/README.md \
  --exclude .github/workflows/README.md \
  --exclude .github/workflows/publish-to-pypi.yml \
  --exclude .github/workflows/smoke-test.yml \
  "$@"
