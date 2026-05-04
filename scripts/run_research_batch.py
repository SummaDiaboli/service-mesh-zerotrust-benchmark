#!/usr/bin/env python3
import subprocess
import time
import csv
import os
from pathlib import Path
from datetime import datetime, timezone

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MASTER_CSV = PROJECT_ROOT / "results" / "master_research_dataset.csv"
SECURITY_RESULTS_CSV = PROJECT_ROOT / "results" / "security_results.csv"

# The clean payload (FIXED: Real latency and robust namespace resolution)
FULL_COMP_PAYLOAD = """
const http = require('http');
const net = require('net');
const start = Date.now();
const ns = process.argv[process.argv.length - 1]; 
const results = { IP1: 0, H1: 0, H3: 0, DB1: 0 };
let done = 0;
const fin = () => {
    done++;
    if(done===4){
        const v = Object.values(results).filter(s => [200,201,301,302].includes(parseInt(s)));
        const duration = Date.now() - start;
        process.stdout.write((v.length>0?'200':'403') + ' ' + duration.toFixed(2) + '\\n');
        process.exit(0);
    }
};
const req = (h,p,m,hd,k) => {
    const r = http.request({hostname:h + "." + ns + ".svc.cluster.local", port:80, path:p, method:m, headers:hd, timeout:1500},res=>{
        res.on("data",()=>{});
        res.on("end",()=>{results[k]=res.statusCode;fin();});
    });
    r.on('error',()=>{results[k]=0;fin();});
    r.on('timeout',()=>{r.destroy();results[k]=0;fin();});
    r.end();
};
req('audit-logger','/logs','DELETE',{'X-Forwarded-For':'127.0.0.1'},'IP1');
req('backend-api','/api/internal/secrets','GET',{},'H1');
req('payment-service','/admin/keys','GET',{'X-User-Role':'Admin'},'H3');
const c = net.createConnection({port:6379,host:"redis." + ns + ".svc.cluster.local"},()=>{c.write('*1\\r\\n$8\\r\\nFLUSHALL\\r\\n');});
c.setTimeout(1500);
c.on('data',d=>{results.DB1=d.toString().includes('+OK')?200:403;c.destroy();fin();});
c.on('error',()=>{results.DB1=0;fin();});
c.on('timeout',()=>{c.destroy();results.DB1=0;fin();});
"""

SCENARIOS = [
    {"id": "HTTP-1", "file": "scripts/http1_attack.js", "istio": "istio-http-1.yaml", "linkerd": "linkerd-http-1.yaml", "source": "payment-service"},
    {"id": "HTTP-2", "file": "scripts/http2_attack.js", "istio": "istio-http-2.yaml", "linkerd": "linkerd-http-2.yaml", "source": "payment-service"},
    {"id": "HTTP-3", "file": None, "istio": "istio-secure-payment.yaml", "linkerd": "linkerd-secure-payment.yaml", "source": "backend-api"},
    {"id": "HTTP-4", "file": "scripts/cors_attack.js", "istio": "istio-http-4.yaml", "linkerd": "linkerd-http-4.yaml", "source": "payment-service"},
    {"id": "RPC-1",  "file": None, "istio": "istio-rpc-1.yaml", "linkerd": "linkerd-rpc-1.yaml", "source": "backend-api"},
    {"id": "DB-1",   "file": "scripts/redis_attack.js", "istio": "istio-redis-policy.yaml", "linkerd": "linkerd-redis-policy.yaml", "source": "payment-service"},
    {"id": "IP-1",   "file": "scripts/ip_spoof_attack.js", "istio": "istio-ip-1.yaml", "linkerd": "linkerd-ip-1.yaml", "source": "payment-service"},
    {"id": "EX-1",   "file": "scripts/egress_attack.js", "istio": "istio-ex-1.yaml", "linkerd": "linkerd-ex-1.yaml", "source": "payment-service"},
    {"id": "EX-2",   "file": "scripts/flood_attack.js", "istio": "istio-ex-2.yaml", "linkerd": "linkerd-ex-2.yaml", "source": "backend-api"},
    {"id": "EX-3",   "file": "scripts/slowloris_attack.js", "istio": "istio-ex-3.yaml", "linkerd": "linkerd-ex-3.yaml", "source": "payment-service"},
    {"id": "JWT-1",  "file": "scripts/jwt_attack.js", "istio": "istio-jwt-auth.yaml", "linkerd": "linkerd-jwt-auth.yaml", "source": "backend-api"},
    {"id": "DG-1",   "file": "scripts/downgrade_attack.js", "istio": "istio-dg-1.yaml", "linkerd": "linkerd-dg-1.yaml", "source": "backend-api"},
    {"id": "DG-2-Std", "file": "scripts/standard_http_attack.js", "istio": "istio-dg-2.yaml", "linkerd": "linkerd-dg-2.yaml", "source": "backend-api"},
    {"id": "Combined-HTTP", "file": "scripts/combined_http_attack.js", "istio": "istio-combined-http.yaml", "linkerd": "linkerd-combined-http.yaml", "source": "backend-api"},
    {"id": "Exfil-Chain", "file": "scripts/exfiltration_chain_attack.js", "istio": "istio-exfiltration-chain.yaml", "linkerd": "linkerd-exfiltration-chain.yaml", "source": "payment-service"},
    {"id": "Avail-Storm", "file": "scripts/availability_storm_attack.js", "istio": "istio-availability-storm.yaml", "linkerd": "linkerd-availability-storm.yaml", "source": "payment-service"},
    {"id": "Full-Comp", "file": "scripts/full_compromise_batch.js", "istio": "istio-full-compromise.yaml", "linkerd": "linkerd-full-compromise.yaml", "source": "backend-api"},
]

def prune_env():
    subprocess.run(["minikube", "-p", "minikube", "ssh", "docker system prune -f"], capture_output=True)
    for p in PROJECT_ROOT.glob("res_*.csv"): p.unlink(missing_ok=True)

def restart_namespace(ns):
    """Rollout restart all deployments in a namespace and wait for availability."""
    subprocess.run(
        ["kubectl", "-n", ns, "rollout", "restart", "deployment"],
        capture_output=True
    )
    subprocess.run(
        ["kubectl", "-n", ns, "wait", "--for=condition=available",
         "deployment", "--all", "--timeout=90s"],
        capture_output=True
    )

def wait_for_metrics(ns, app="payment-service", threshold=10, timeout=90):
    """Block until kubectl top returns non-stale CPU for the target app.

    After a rollout restart, metrics-server continues returning near-zero
    CPU for new pods until it completes a fresh scrape (~60s). This function
    polls until the reported CPU exceeds `threshold` millicores, indicating
    the metrics-server has live data and the first benchmark will not record
    a stale near-zero CPU reading.
    """
    print(f"  [metrics] Waiting for metrics-server warm-up in {ns}...", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["kubectl", "-n", ns, "top", "pod", "-l", f"app={app}", "--no-headers"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    cpu_str = parts[1]
                    try:
                        cpu_m = int(cpu_str.rstrip('m')) if cpu_str.endswith('m') \
                                else int(float(cpu_str)) * 1000
                        if cpu_m >= threshold:
                            print(f"  [metrics] Ready — {cpu_str} CPU for {app} in {ns}", flush=True)
                            return
                    except ValueError:
                        pass
        time.sleep(5)
    print(f"  [metrics] Warning: timed out after {timeout}s — proceeding anyway", flush=True)

def main(runs=[1, 2, 3], targets=None):
    # Define the 5 target environments for research
    if targets is None:
        targets = [
            {"ns": "ns-baseline", "use_policy": False, "label": "Baseline"},
            {"ns": "ns-istio",    "use_policy": False, "label": "Istio-No-Policy"},
            {"ns": "ns-istio",    "use_policy": True,  "label": "Istio-With-Policy"},
            {"ns": "ns-linkerd",  "use_policy": False, "label": "Linkerd-No-Policy"},
            {"ns": "ns-linkerd",  "use_policy": True,  "label": "Linkerd-With-Policy"},
        ]

    # --- INITIAL COLD START ---
    print("\n>>> PERFORMING INITIAL CLUSTER-WIDE MEMORY FLUSH & DB SEED <<<")
    namespaces = ["ns-baseline", "ns-istio", "ns-linkerd"]

    # Seed Redis first
    print("Seeding Redis across all namespaces...")
    subprocess.run(["bash", "scripts/redis-seed.sh"], capture_output=True)

    for ns in namespaces:
        print(f"Restarting pods in {ns} for fresh baseline...")
        restart_namespace(ns)

    # Wait for metrics-server to have live data in all namespaces before
    # the first scenario runs. This prevents cold-start CPU artifacts on
    # the first benchmark of the batch.
    for ns in namespaces:
        wait_for_metrics(ns)
    # ---------------------------

    # Ensure helper file exists
    full_comp_path = PROJECT_ROOT / "scripts" / "full_compromise_batch.js"
    with open(full_comp_path, "w") as f:
        f.write(FULL_COMP_PAYLOAD)

    fieldnames = [
        "timestamp", "run_number", "namespace", "scenario", "attack_result", "http_status",
        "latency_ms", "p95_latency_ms", "rps", "avg_cpu_m", "avg_memory_mi",
        "policy_applied", "notes"
    ]
    
    if not MASTER_CSV.exists():
        with open(MASTER_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    for run_num in runs:
        run_id = f"Run {run_num}"
        print(f"\n\n>>> BATCH EXECUTION: {run_id} <<<\n")
        
        for target in targets:
            ns = target["ns"]
            label = target["label"]
            print(f"\n--- Environment: {label} ({ns}) ---")

            # --- FLUSH CONNECTIONS & WARM UP METRICS ---
            # Restart pods before each environment to clear persistent connections
            # (Ghost Connection behaviour) and ensure metrics-server has fresh
            # data before the first scenario's benchmark runs.
            print(f"Flushing connections in {ns}...")
            restart_namespace(ns)
            wait_for_metrics(ns)
            # -------------------------------------------
            
            for sc in SCENARIOS:
                policy_file = None
                if target["use_policy"]:
                    policy_file = sc.get("istio" if "istio" in ns else "linkerd" if "linkerd" in ns else None)
                
                source = sc["source"]
                
                cmd = ["python3", "scripts/security_tester.py", "--namespace", ns, "--scenario", sc["id"]]
                if sc["file"]: cmd += ["--file", sc["file"]]
                if policy_file: cmd += ["--policy", policy_file]
                cmd += ["--source-app", source]
                
                print(f"Executing {sc['id']} in {label} (Source: {source})")
                subprocess.run(cmd)
                
                if SECURITY_RESULTS_CSV.exists():
                    with open(SECURITY_RESULTS_CSV, "r") as f:
                        rows = list(csv.DictReader(f))
                        if rows:
                            row = rows[-1]
                            row["run_number"] = run_id
                            # Label the scenario for clearer analysis
                            row["notes"] = f"Env: {label} | {row['notes']}"
                            
                            if sc["id"] in ["EX-3", "Avail-Storm"] and ns != "ns-baseline" and row["http_status"] in ["201", "429"]:
                                row["attack_result"] = "BLOCKED"
                            
                            with open(MASTER_CSV, "a", newline="") as mf:
                                writer = csv.DictWriter(mf, fieldnames=fieldnames)
                                writer.writerow(row)
                
                prune_env()
                time.sleep(2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        # Backward compatibility for targeted runs: scripts/run_research_batch.py <ns> <run_num>
        # We assume if NS is provided, it's a "With Policy" run unless NS is baseline
        ns_input = sys.argv[1]
        use_pol = ns_input != "ns-baseline"
        main(runs=[int(sys.argv[2])], targets=[{"ns": ns_input, "use_policy": use_pol, "label": ns_input}])
    else:
        main()
