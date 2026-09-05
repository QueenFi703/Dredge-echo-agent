#!/bin/bash
# Health Check - Validates system readiness
# Usage: health-check.sh [--phase <name>] [--strict]

set -euo pipefail

# Default values
PHASE="general"
STRICT_MODE=false
MIN_DISK_GB=5
MIN_MEMORY_MB=500

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --phase)
      PHASE="$2"
      shift 2
      ;;
    --strict)
      STRICT_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Running health check for phase: $PHASE"

# Check disk space
DISK_AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
echo "Disk available: ${DISK_AVAILABLE}GB"

if [[ $DISK_AVAILABLE -lt $MIN_DISK_GB ]]; then
  echo "WARNING: Low disk space (${DISK_AVAILABLE}GB < ${MIN_DISK_GB}GB)"
  if [[ "$STRICT_MODE" == "true" ]]; then
    exit 1
  fi
fi

# Check memory
if [[ "$OSTYPE" == "darwin"* ]]; then
  MEMORY_AVAILABLE=$(vm_stat | grep "Pages free" | awk '{print int($3 * 4096 / 1024 / 1024)}')
else
  MEMORY_AVAILABLE=$(free -m | awk 'NR==2 {print $7}')
fi

echo "Memory available: ${MEMORY_AVAILABLE}MB"

if [[ $MEMORY_AVAILABLE -lt $MIN_MEMORY_MB ]]; then
  echo "WARNING: Low memory (${MEMORY_AVAILABLE}MB < ${MIN_MEMORY_MB}MB)"
  if [[ "$STRICT_MODE" == "true" ]]; then
    exit 1
  fi
fi

# Check required commands
REQUIRED_COMMANDS=("bash" "date" "awk")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "ERROR: Required command not found: $cmd"
    exit 1
  fi
done

echo "Health check passed for phase: $PHASE"
