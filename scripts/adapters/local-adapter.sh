#!/bin/bash
# Local Adapter - Development machine context wrapper
# Adapts core scripts for local development environment

set -euo pipefail

# Local development setup
export METRICS_DIR="${METRICS_DIR:-.local-metrics}"
export WORKING_DIR="${WORKING_DIR:-.}"

# Ensure metrics directory exists
mkdir -p "$METRICS_DIR"

# Forward to core scripts with local-specific context
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../core" && pwd)"

case "${1:-}" in
  phase-runner)
    shift
    exec bash "$SCRIPT_DIR/phase-runner.sh" "$@"
    ;;
  metric-collector)
    shift
    exec bash "$SCRIPT_DIR/metric-collector.sh" "$@"
    ;;
  health-check)
    shift
    exec bash "$SCRIPT_DIR/health-check.sh" "$@"
    ;;
  deploy)
    shift
    exec bash "$SCRIPT_DIR/deploy.sh" "$@"
    ;;
  *)
    echo "Usage: local-adapter.sh <phase-runner|metric-collector|health-check|deploy> [args...]"
    exit 1
    ;;
esac
