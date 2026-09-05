#!/bin/bash
# Docker Adapter - Container context wrapper
# Adapts core scripts for Docker container environment

set -euo pipefail

# Docker-specific setup
export METRICS_DIR="${METRICS_DIR:-/metrics}"
export WORKING_DIR="${WORKING_DIR:-/workspace}"

# Ensure directories exist
mkdir -p "$METRICS_DIR"
mkdir -p "$WORKING_DIR"

# Forward to core scripts with Docker-specific context
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
    echo "Usage: docker-adapter.sh <phase-runner|metric-collector|health-check|deploy> [args...]"
    exit 1
    ;;
esac
