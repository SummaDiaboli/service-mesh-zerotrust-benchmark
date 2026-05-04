#!/bin/bash
set -e

# reset-environment.sh
# Performs a full reset of the thesis environment to a baseline state.
# Clears policies, rebuilds services, and reseeds data.

# Navigate to the project root (one level up from this script)
cd "$(dirname "$0")/.."

echo "STARTING FULL ENVIRONMENT RESET"

# 1. Clear existing L7 policies (Istio & Linkerd)
echo "Step 1: Clearing policies from all namespaces..."
for ns in "ns-baseline" "ns-istio" "ns-linkerd"; do
    ./scripts/reset-policies.sh "$ns"
done

# 2. Re-apply Manifests to ensure latest configuration
echo "Step 2: Re-applying Kubernetes manifests..."
for ns in "ns-baseline" "ns-istio" "ns-linkerd"; do
    kubectl apply -f k8s/ -n "$ns"
done

# 3. Rebuild and restart services
echo "Step 3: Rebuilding all microservices..."
./scripts/rebuild_backend.sh
./scripts/rebuild_frontend.sh
./scripts/rebuild_audit_logger.sh
./scripts/rebuild_payment_service.sh

# 3. Wait for the rollouts to complete
echo "Step 3: Waiting for services to reach ready state..."
for ns in "ns-baseline" "ns-istio" "ns-linkerd"; do
    echo "Checking $ns..."
    kubectl wait --for=condition=available --timeout=60s deployment --all -n "$ns"
done

# 4. Reseed the database
# This script handles the FLUSHALL and injection for all namespaces.
echo "Step 4: Reseeding Redis databases..."
./scripts/redis-seed.sh

echo "ENVIRONMENT RESET COMPLETE"
