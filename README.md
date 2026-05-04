# Service Mesh Zero Trust Benchmark

**Comparative Analysis of Zero Trust in Microservices using Service Mesh**
*Quantifying the Security Efficacy and Performance Overhead of Layer 7 Authorization Policies in Istio and Linkerd*

Salim Hussaini, Ramzi Samir Masoud Abu Zahra — University West, 2026

This repository contains the experimental testbed for the thesis. It includes the microservices stack, all 34 security policy files (17 Istio + 17 Linkerd), and the research orchestration scripts. The study evaluates Layer 7 security efficacy and performance overhead across Istio and Linkerd service meshes against a bare Kubernetes baseline, executing 153 experimental cycles (17 attack scenarios × 3 environments × 3 runs) under an Assume Breach threat model.

Link to published thesis: *to be added on publication*

---

## Software Versions

| Component | Version |
|:----------|:--------|
| Minikube | v1.38.0 |
| Kubernetes | v1.35.0 |
| Istio | v1.28.3 (Minimal Profile) |
| Linkerd | edge-26.1.4 |
| Frontend | React v19.2.0, Vite v7.2.4, Tailwind CSS v4.1.18 |
| Backend API | Node.js v20.20.0 (Express) |
| Audit Logger | Go v1.23 (Fiber) |
| Database | Redis v7.x (alpine) |
| Package manager | pnpm |

---

## Repository Structure

```
.
├── audit-logger/             # Go/Fiber audit logging service
├── backend/                  # Node.js/Express API and payment service
├── frontend/                 # React/Vite frontend
├── k8s/                      # Kubernetes manifests
│   ├── api-deployment.yaml
│   ├── payment-deployment.yaml
│   ├── audit-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── redis-deployment.yaml
├── policies/                 # L7 security policy files (34 total)
│   ├── istio-*.yaml          # AuthorizationPolicy, RequestAuthentication, EnvoyFilter, ServiceEntry
│   └── linkerd-*.yaml        # Server, AuthorizationPolicy, HTTPRoute, HTTPLocalRateLimitPolicy
└── scripts/
    ├── run_research_batch.py     # Master orchestrator (5 envs × 17 scenarios × 3 runs)
    ├── security_tester.py        # Per-scenario runner (policy → attack → k6 → reset)
    ├── analyze_dataset.py        # Aggregates raw CSV into statistical summary
    ├── generate_results_typ.py   # Generates results chapter from statistical CSV
    ├── load-test.js              # k6 load test (50 VU, 30s)
    ├── monitor-resources.sh      # Background CPU/memory scraper during k6 runs
    ├── reset-policies.sh         # Tears down all policies in a namespace
    ├── reset-environment.sh      # Full environment reset
    ├── reset-data.sh             # Data reset utility
    └── *_attack.js               # Attack scripts (one per scenario)
```

---

## Prerequisites

- **Docker** — for Minikube driver and image builds
- **Minikube** v1.38.0
- **kubectl**
- **istioctl** v1.28.3 — [istio.io/downloadIstio](https://istio.io/downloadIstio)
- **Linkerd CLI** edge-26.1.4 — `curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh`
- **k6** — [k6.io/docs/get-started/installation](https://k6.io/docs/get-started/installation)
- **Node.js** v20
- **Python 3**
- **pnpm** — `npm install -g pnpm`

---

## Setup

### 1. Start Minikube

```bash
minikube start --cpus 4 --memory 8192 --driver=docker
```

### 2. Install Istio

```bash
istioctl install --set profile=minimal -y
```

### 3. Install Linkerd

```bash
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -
linkerd check
```

### 4. Create Namespaces and Enable Injection

```bash
kubectl create namespace ns-baseline
kubectl create namespace ns-istio
kubectl create namespace ns-linkerd

kubectl label namespace ns-istio istio-injection=enabled
kubectl annotate namespace ns-linkerd linkerd.io/inject=enabled
```

### 5. Build Docker Images

Images must be built into Minikube's Docker daemon:

```bash
eval $(minikube docker-env)

docker build -t thesis-backend:latest ./backend
docker build -t thesis-audit:latest ./audit-logger
docker build -t thesis-frontend:latest ./frontend
```

### 6. Deploy Application Stack

```bash
for ns in ns-baseline ns-istio ns-linkerd; do
  kubectl apply -f k8s/ -n $ns
done
```

Verify all pods are running:

```bash
kubectl get pods -n ns-baseline
kubectl get pods -n ns-istio
kubectl get pods -n ns-linkerd
```

---

## Running the Experiment

### Full Batch (153 cycles)

Runs all 17 scenarios across all 5 environments (Baseline, Istio No-Policy, Istio With-Policy, Linkerd No-Policy, Linkerd With-Policy) for 3 complete runs. Each cycle applies the policy, executes the attack, runs a 30-second k6 load test at 50 VUs, records CPU and memory, then resets.

```bash
python3 scripts/run_research_batch.py
```

Output is written to `results/master_research_dataset.csv`. A full 3-run batch takes several hours.

### Single Scenario

```bash
python3 scripts/security_tester.py \
  --namespace ns-istio \
  --scenario HTTP-1 \
  --file policies/istio-http-1.yaml \
  --policy istio \
  --source-app payment-service
```

### Reset Policies

```bash
bash scripts/reset-policies.sh ns-istio
bash scripts/reset-policies.sh ns-linkerd
```

---

## Regenerating the Statistical Summary

After collecting raw data, aggregate it into the statistical summary:

```bash
python3 scripts/analyze_dataset.py
```

This reads `results/master_research_dataset.csv` and produces `results/scenario_statistical_analysis.csv` (17 scenarios × 5 environments, with mode results and averaged metrics).

---

## Key Findings

| Metric | Istio | Linkerd | Baseline |
|:-------|:------|:--------|:---------|
| Scenarios blocked (of 17) | 15 | 11 | 0 |
| Typical p95 latency overhead | ~90ms above baseline | ~10-15ms above baseline | reference |
| Memory, hardened state (avg) | 119.14 MiB | 129.38 MiB | 27.66 MiB |
| EX-2 p95 under active rate limiting | 9.59ms at 9,025 RPS | 6.64ms at 10,882 RPS | reference |
| Failure mode under extreme load | Fail-slow (observable signal) | Fail-open (silent at ~14k RPS) | reference |

Both meshes share two hard limits regardless of policy configuration:

- **Protocol Sniffing Blind Spot**: raw TCP non-HTTP protocols bypass L7 filter chains entirely (demonstrated in DB-1).
- **Ghost Connections**: active Keep-Alive connections bypass newly applied policies until a rollout restart is performed.
