#!/bin/bash

# Default to ns-baseline if no argument provided
NAMESPACE="${1:-ns-baseline}"

echo "RESETTING STATE: Deleting all L7 Policies in $NAMESPACE..."

# --- ISTIO RESOURCES ---
echo "   - Removing Istio AuthorizationPolicies..."
# Use the full FQDN to bypass alias issues
kubectl delete authorizationpolicies.security.istio.io --all -n "$NAMESPACE" --ignore-not-found

echo "   - Removing other Istio resources..."
kubectl delete virtualservices.networking.istio.io --all -n "$NAMESPACE" --ignore-not-found
kubectl delete destinationrules.networking.istio.io --all -n "$NAMESPACE" --ignore-not-found
kubectl delete peerauthentications.security.istio.io --all -n "$NAMESPACE" --ignore-not-found
kubectl delete envoyfilters.networking.istio.io --all -n "$NAMESPACE" --ignore-not-found

#echo "   - Removing Istio VirtualServices..."
#kubectl delete virtualservices --all -n "$NAMESPACE" --ignore-not-found
#echo "   - Removing Istio DestinationRules..."
#kubectl delete destinationrules --all -n "$NAMESPACE" --ignore-not-found
#echo "   - Removing Istio AuthorizationPolicies..."
#kubectl delete authorizationpolicies --all -n "$NAMESPACE" --ignore-not-found
#echo "   - Removing Istio PeerAuthentication..."
#kubectl delete peerauthentications --all -n "$NAMESPACE" --ignore-not-found
#echo "   - Removing Istio RequestAuthentication..."
#kubectl delete requestauthentications --all -n "$NAMESPACE" --ignore-not-found
#echo "   - Removing Istio EnvoyFilters..."
#kubectl delete envoyfilters --all -n "$NAMESPACE" --ignore-not-found

# --- LINKERD RESOURCES ---
echo "   - Removing Linkerd Servers..."
kubectl delete server --all -n "$NAMESPACE" --ignore-not-found
echo "   - Removing Linkerd Authorizations..."
kubectl delete serverauthorization --all -n "$NAMESPACE" --ignore-not-found
echo "   - Removing Linkerd AuthorizationPolicies..."
kubectl delete authorizationpolicy.policy.linkerd.io --all -n "$NAMESPACE" --ignore-not-found
echo "   - Removing Linkerd HTTPRoutes..."
kubectl delete httproute.policy.linkerd.io --all -n "$NAMESPACE" --ignore-not-found
echo "   - Removing Linkerd NetworkAuthentications..."
kubectl delete networkauthentication.policy.linkerd.io --all -n "$NAMESPACE" --ignore-not-found
echo "   - Removing Linkerd RateLimitPolicies..."
kubectl delete httplocalratelimitpolicy.policy.linkerd.io --all -n "$NAMESPACE" --ignore-not-found

echo "🔍 Verifying clean state..."
REMAINING=$(kubectl get authorizationpolicies -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l)
if [ "$REMAINING" -eq 0 ]; then
  echo "DONE. Namespace $NAMESPACE is now in BASELINE state."
else
  echo "⚠️ WARNING: $REMAINING policies still exist in $NAMESPACE!"
fi
