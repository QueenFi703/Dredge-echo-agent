#!/bin/bash
# deploy.sh — Build and validate the Aster language package
# Usage: deploy.sh [--env <staging|production>] [--skip-build]
#
# Phases followed: init → validate → build → verify → report
# Conforms to the fractal operational cadence of this repository.

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
DEPLOY_ENV="${DEPLOY_ENV:-production}"
SKIP_BUILD="${SKIP_BUILD:-false}"
METRICS_DIR="${METRICS_DIR:-.metrics}"
DIST_DIR="dist"
START_TIME=$(date +%s)

# ── Parse arguments ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      DEPLOY_ENV="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

mkdir -p "$METRICS_DIR"

echo "=== Aster Deployment ==="
echo "Environment : $DEPLOY_ENV"
echo "Started at  : $(date -Iseconds)"
echo ""

# ── Phase 1: Validate environment ───────────────────────────────────────────────
echo "--- Phase: validate ---"

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is not available"
  exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Python      : $PYTHON_VERSION"

if ! python3 -c "import language" 2>/dev/null; then
  echo "ERROR: 'language' package is not importable — run 'pip install -e .' first"
  exit 1
fi

echo "Import check: OK"

# ── Phase 2: Build ──────────────────────────────────────────────────────────────
if [[ "$SKIP_BUILD" != "true" ]]; then
  echo ""
  echo "--- Phase: build ---"

  if ! python3 -c 'import build' 2>/dev/null; then
    python3 -m pip install --quiet build
  fi

  python3 -m build --outdir "$DIST_DIR"
  echo "Build       : OK — artifacts in $DIST_DIR/"
  ls -lh "$DIST_DIR"/
fi

# ── Phase 3: Verify package contents ────────────────────────────────────────────
echo ""
echo "--- Phase: verify ---"

# Verify core modules are importable
# Keep this list in sync with the packages declared in pyproject.toml
for module in language.parser language.semantics language.runtime compiler.transpiler bridge.python_adapter; do
  if python3 -c "import $module" 2>/dev/null; then
    echo "Module OK   : $module"
  else
    echo "ERROR: Module not importable: $module"
    exit 1
  fi
done

# Run a minimal smoke-test: parse and execute a simple .co program
SMOKE_RESULT=$(python3 - << 'PYEOF'
from language.runtime.interpreter import Interpreter

SOURCE = """
entity data
entity model
action train(data -> model)
cycle training {
    train
}
"""

interpreter = Interpreter()
result = interpreter.run(SOURCE)
assert len(result.execution_log) > 0, "Execution log should not be empty"
print("smoke-test=passed")
PYEOF
)

if [[ "$SMOKE_RESULT" == *"smoke-test=passed"* ]]; then
  echo "Smoke test  : PASSED"
else
  echo "ERROR: Smoke test failed"
  exit 1
fi

# ── Phase 4: Record metrics ──────────────────────────────────────────────────────
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

cat > "$METRICS_DIR/deploy-metrics.json" << EOF
{
  "phase": "deploy",
  "environment": "$DEPLOY_ENV",
  "status": "success",
  "duration_seconds": $DURATION,
  "timestamp": "$(date -Iseconds)"
}
EOF

echo ""
echo "=== Deployment complete ==="
echo "Environment : $DEPLOY_ENV"
echo "Duration    : ${DURATION}s"
echo "Metrics     : $METRICS_DIR/deploy-metrics.json"
