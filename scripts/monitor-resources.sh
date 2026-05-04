#!/bin/bash
NAMESPACE=$1
OUTPUT_FILE=$2

# 1. Wait for Metrics API to be available (Timeout after 60s)
echo "   ... Waiting for Metrics API..."
for i in {1..60}; do
  if kubectl top pod -n "$NAMESPACE" &>/dev/null; then
    break
  fi
  sleep 1
done

# If it failed after 60s, exit (don't spam errors)
if ! kubectl top pod -n "$NAMESPACE" &>/dev/null; then
  echo "⚠️  METRICS API NOT AVAILABLE. Skipping resource monitoring."
  exit 0
fi

# 2. Start Monitoring Loop
echo "Timestamp,Pod_Name,CPU(m),Memory(Mi)" >"$OUTPUT_FILE"

while true; do
  TIMESTAMP=$(date +%H:%M:%S)

  # Run kubectl top (suppress errors if a pod is terminating)
  kubectl top pod -n "$NAMESPACE" -l app=payment-service --no-headers 2>/dev/null | while read line; do
    POD=$(echo "$line" | awk '{print $1}')
    CPU=$(echo "$line" | awk '{print $2}' | sed 's/m//g')  # Strip unit 'm'
    MEM=$(echo "$line" | awk '{print $3}' | sed 's/Mi//g') # Strip unit 'Mi'

    echo "$TIMESTAMP,$POD,$CPU,$MEM" >>"$OUTPUT_FILE"
  done

  sleep 1
done
