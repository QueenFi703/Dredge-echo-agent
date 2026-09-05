#!/bin/bash
# Metric Collector - Gathers and records system metrics
# Usage: metric-collector.sh --type <resource|timing|outcome> [--output <file>]

set -euo pipefail

# Default values
METRIC_TYPE="resource"
OUTPUT_FILE=".metrics/metrics.json"
TIMESTAMP=$(date -Iseconds)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      METRIC_TYPE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create metrics directory
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Collect metrics based on type
case $METRIC_TYPE in
  resource)
    # Disk space
    DISK_AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    
    # Memory
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      MEMORY_AVAILABLE=$(vm_stat | grep "Pages free" | awk '{print int($3 * 4096 / 1024 / 1024)}')
    else
      # Linux
      MEMORY_AVAILABLE=$(free -m | awk 'NR==2 {print $7}')
    fi
    
    # CPU usage
    if command -v top &> /dev/null; then
      CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")
    else
      CPU_USAGE="0"
    fi
    
    cat > "$OUTPUT_FILE" << EOF
{
  "type": "resource",
  "timestamp": "$TIMESTAMP",
  "metrics": {
    "disk_available_gb": $DISK_AVAILABLE,
    "memory_available_mb": ${MEMORY_AVAILABLE:-0},
    "cpu_usage_percent": ${CPU_USAGE:-0}
  }
}
EOF
    ;;
    
  timing)
    cat > "$OUTPUT_FILE" << EOF
{
  "type": "timing",
  "timestamp": "$TIMESTAMP",
  "metrics": {
    "recorded_at": "$TIMESTAMP"
  }
}
EOF
    ;;
    
  outcome)
    cat > "$OUTPUT_FILE" << EOF
{
  "type": "outcome",
  "timestamp": "$TIMESTAMP",
  "metrics": {
    "recorded_at": "$TIMESTAMP"
  }
}
EOF
    ;;
    
  *)
    echo "Unknown metric type: $METRIC_TYPE"
    exit 1
    ;;
esac

echo "Metrics collected: $METRIC_TYPE"
cat "$OUTPUT_FILE"
