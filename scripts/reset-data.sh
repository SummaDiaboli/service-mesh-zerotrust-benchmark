#!/bin/bash

NAMESPACE="${1:-ns-baseline}"

echo "RESETTING DATA: Flushing Redis Database in $NAMESPACE..."

# We use the redis-cli inside the pod to run FLUSHALL
# We find the pod name dynamically using labels
REDIS_POD=$(kubectl get pod -l app=redis -n "$NAMESPACE" -o jsonpath="{.items[0].metadata.name}")

if [ -z "$REDIS_POD" ]; then
  echo "ERROR: Redis pod not found in $NAMESPACE"
  exit 1
fi

kubectl exec -n "$NAMESPACE" "$REDIS_POD" -c redis -- redis-cli FLUSHALL

echo "DONE. Redis database is empty."
