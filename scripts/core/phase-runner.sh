#!/bin/bash
# Phase Runner - Universal phase execution pattern
# Usage: phase-runner.sh --phase <name> --command <cmd> [--timeout <seconds>]

set -euo pipefail

# Default values
PHASE=""
COMMAND=""
TIMEOUT=300
WORKING_DIR="${WORKING_DIR:-.}"
METRICS_DIR="${METRICS_DIR:-.metrics}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --phase)
      PHASE="$2"
      shift 2
      ;;
    --command)
      COMMAND="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required arguments
if [[ -z "$PHASE" ]]; then
  echo "Error: --phase is required"
  exit 1
fi

# Create metrics directory
mkdir -p "$METRICS_DIR"

# Record phase start
PHASE_START=$(date +%s)
echo "Starting phase: $PHASE at $(date -Iseconds)"
echo "$PHASE_START" > "$METRICS_DIR/phase-${PHASE}-start.txt"

# Execute command if provided
if [[ -n "$COMMAND" ]]; then
  echo "Executing: $COMMAND"
  
  # Run with timeout
  if timeout "$TIMEOUT" bash -c "$COMMAND"; then
    PHASE_STATUS="success"
    EXIT_CODE=0
  else
    PHASE_STATUS="failure"
    EXIT_CODE=$?
  fi
else
  PHASE_STATUS="success"
  EXIT_CODE=0
fi

# Record phase end
PHASE_END=$(date +%s)
PHASE_DURATION=$((PHASE_END - PHASE_START))

echo "Phase $PHASE completed with status: $PHASE_STATUS"
echo "Duration: ${PHASE_DURATION}s"

# Write metrics
cat > "$METRICS_DIR/phase-${PHASE}-metrics.json" << EOF
{
  "phase": "$PHASE",
  "status": "$PHASE_STATUS",
  "exit_code": $EXIT_CODE,
  "start_time": $PHASE_START,
  "end_time": $PHASE_END,
  "duration_seconds": $PHASE_DURATION,
  "timestamp": "$(date -Iseconds)"
}
EOF

exit $EXIT_CODE
