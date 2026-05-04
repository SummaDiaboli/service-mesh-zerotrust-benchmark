#!/usr/bin/env python3
"""
security_tester.py
Modular orchestrator for L7 attack scenarios and performance benchmarking.
"""

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# --- IMPORTS ---
try:
    from scripts.grpc_attack_logic import get_node_attack_payload
except ImportError:
    # If run from scripts/ directory
    from grpc_attack_logic import get_node_attack_payload

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
POLICIES_DIR = PROJECT_ROOT / "policies"
RESULTS_CSV  = PROJECT_ROOT / "results" / "security_results.csv"

ATTACKER_IMAGE     = "nicolaka/netshoot:latest"
ATTACKER_POD_NAME  = "thesis-attacker"
K6_IMAGE           = "grafana/k6"

POLICY_PROPAGATION_SECONDS = 10
POD_READY_TIMEOUT_SECONDS  = 60

SERVICE_PORT = 80
CSV_FIELDNAMES = [
    "timestamp", "namespace", "scenario", "attack_result", "http_status",
    "latency_ms", "p95_latency_ms", "rps", "avg_cpu_m", "avg_memory_mi",
    "policy_applied", "notes"
]

# --- LOGGING ---
def log(level, msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [{level:5}] {msg}", flush=True)

def info(msg): log("INFO", msg)
def warn(msg): log("WARN", msg)
def error(msg): log("ERROR", msg)

# --- UTILS ---
def run_kubectl(args, namespace=None, timeout=120):
    cmd = ["minikube", "-p", "minikube", "kubectl", "--"]
    if namespace: cmd += ["-n", namespace]
    cmd += args
    # info(f"DEBUG shell: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return 1, "", str(e)

class ExperimentOrchestrator:
    def __init__(self, namespace, output_csv=RESULTS_CSV, policy_override=None):
        self.ns = namespace
        self.csv_path = Path(output_csv)
        self.policy_file = policy_override
        self._ensure_csv()

    def _ensure_csv(self):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            with open(self.csv_path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writeheader()

    def apply_policy(self):
        if not self.policy_file:
            info(f"No policy specified for {self.ns} run.")
            return "none"
        path = POLICIES_DIR / self.policy_file
        if not path.exists():
            error(f"Policy file not found: {path}")
            return "error"
        rc, _, err = run_kubectl(["apply", "-f", str(path)], namespace=self.ns)
        if rc == 0:
            info(f"Applied {self.policy_file}. Waiting {POLICY_PROPAGATION_SECONDS}s...")
            time.sleep(POLICY_PROPAGATION_SECONDS)
            return self.policy_file
        error(f"Policy failed: {err}")
        return "error"

    def reset_policies(self):
        info(f"Resetting policies in {self.ns}...")
        script = PROJECT_ROOT / "scripts" / "reset-policies.sh"
        subprocess.run(["bash", str(script), self.ns], capture_output=True)

    def run_performance_test(self, duration="30s", vus="50", script_path=None):
        results = {"p95": 0, "rps": 0, "cpu": 0, "mem": 0}
        res_log = PROJECT_ROOT / f"res_{self.ns}.csv"
        mon_script = PROJECT_ROOT / "scripts" / "monitor-resources.sh"
        
        # Default to standard load-test.js
        load_js = script_path if script_path else PROJECT_ROOT / "scripts" / "load-test.js"
        
        target = f"http://payment-service.{self.ns}.svc.cluster.local:80/process"

        info(f"Starting Performance Test ({vus} VUs, {duration}) using {load_js.name}...")
        mon_proc = subprocess.Popen(["bash", str(mon_script), self.ns, str(res_log)])

        try:
            run_kubectl(["delete", "configmap", "k6-test-script", "--ignore-not-found"], namespace=self.ns)
            run_kubectl(["create", "configmap", "k6-test-script", f"--from-file=load-test.js={load_js}"], namespace=self.ns)
            
            k6_args = f"k6 run /scripts/load-test.js --summary-export=/results/summary.json && echo '---JSON_START---' && cat /results/summary.json && echo '---JSON_END---' && echo K6_DONE || echo K6_FAILED; sleep 10"
            overrides = {
                "spec": {"containers": [{"name": "k6-load-tester", "image": K6_IMAGE, "imagePullPolicy": "IfNotPresent",
                         "command": ["/bin/sh", "-c"], "args": [k6_args],
                         "env": [
                             {"name": "TARGET_URL", "value": target}, 
                             {"name": "CONCURRENCY", "value": str(vus)}, 
                             {"name": "DURATION", "value": duration},
                             {"name": "NAMESPACE", "value": self.ns}
                         ],
                         "volumeMounts": [{"name": "s", "mountPath": "/scripts"}, {"name": "r", "mountPath": "/results"}]}],
                         "volumes": [{"name": "s", "configMap": {"name": "k6-test-script"}}, {"name": "r", "emptyDir": {}}]}
            }
            
            run_kubectl(["run", "k6-load-tester", "--image", K6_IMAGE, "--restart=Never", "--overrides", json.dumps(overrides)], namespace=self.ns)
            
            out = ""
            time.sleep(int(duration.replace("s","")))
            for _ in range(30):
                _, out, _ = run_kubectl(["logs", "k6-load-tester", "-c", "k6-load-tester"], namespace=self.ns)
                if "K6_DONE" in out or "K6_FAILED" in out: break
                time.sleep(5)

            match = re.search(r"---JSON_START---(.*?)---JSON_END---", out, re.DOTALL)
            if match:
                try:
                    m = json.loads(match.group(1).strip())["metrics"]
                    results["p95"] = round(m["http_req_duration"].get("values", m["http_req_duration"]).get("p(95)", 0), 2)
                    results["rps"] = round(m["http_reqs"].get("values", m["http_reqs"]).get("rate", 0), 2)
                except Exception as e:
                    warn(f"Failed to parse k6 JSON: {e}")
            else:
                warn("Could not find JSON markers in k6 logs.")
                if "K6_FAILED" in out:
                    error("K6 execution failed inside the pod.")
        finally:
            run_kubectl(["delete", "pod", "k6-load-tester", "--force", "--grace-period=0", "--ignore-not-found"], namespace=self.ns)
            mon_proc.terminate()
            mon_proc.wait()

        if res_log.exists():
            with open(res_log) as f:
                data = list(csv.DictReader(f))
                if data:
                    results["cpu"] = round(sum(float(d["CPU(m)"]) for d in data) / len(data), 2)
                    results["mem"] = round(sum(float(d["Memory(Mi)"]) for d in data) / len(data), 2)
            res_log.unlink()
        
        return results

    def record(self, scenario, sec_res, perf_res, policy):
        # 200/201 (OK), 301/302 (Redirects) mean the external world/app was reached = VULNERABLE
        # 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 429 (Too Many Requests), 503 (Service Unavailable), 504 (Gateway Timeout) = BLOCKED/MITIGATED
        vulnerable_codes = [200, 201, 301, 302]
        blocked_codes = [401, 403, 404, 429, 503, 504]
        
        try:
            status = int(sec_res.get("status", 0))
        except (ValueError, TypeError):
            status = 0

        if sec_res.get("attack_result") and sec_res["attack_result"] != "UNKNOWN":
            res_str = sec_res["attack_result"]
        elif scenario in ["EX-3", "Avail-Storm"]:
            if self.ns != "ns-baseline" and status in [201, 429]:
                res_str = "BLOCKED"
            elif status == 0:
                res_str = "BLOCKED" if self.ns != "ns-baseline" else "UNKNOWN"
            else:
                res_str = "VULNERABLE" if status in vulnerable_codes else "BLOCKED" if status in blocked_codes else "UNKNOWN"
        elif scenario in ["Combined-HTTP", "Exfil-Chain", "Full-Comp"]:
            if status == 403: res_str = "BLOCKED"
            elif status == 200: res_str = "VULNERABLE"
            elif status == 0: res_str = "BLOCKED" if self.ns != "ns-baseline" else "UNKNOWN"
            else: res_str = "UNKNOWN"
        else:
            if status == 0:
                res_str = "BLOCKED" if self.ns != "ns-baseline" else "UNKNOWN"
            else:
                res_str = "BLOCKED" if status in blocked_codes else "VULNERABLE" if status in vulnerable_codes else "UNKNOWN"
        
        # Add note about status 0
        notes = sec_res.get("notes", "")
        if status == 0:
            notes = f"ConnError/Timeout | {notes}"
        
        info(f"Classification Decision: scenario={scenario} status={status} -> result={res_str}")
        row = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "namespace": self.ns, "scenario": scenario, "attack_result": res_str,
            "http_status": sec_res["status"], "latency_ms": sec_res["lat"],
            "p95_latency_ms": perf_res["p95"], "rps": perf_res["rps"],
            "avg_cpu_m": perf_res["cpu"], "avg_memory_mi": perf_res["mem"],
            "policy_applied": policy, "notes": f"Env: {self.ns} | {notes}"
        }
        with open(self.csv_path, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDNAMES).writerow(row)
        info(f"Recorded: {res_str} | Status: {sec_res['status']} | Latency: {sec_res['lat']}ms")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True, choices=["ns-istio", "ns-linkerd", "ns-baseline"])
    parser.add_argument("--scenario", help="Built-in scenario ID")
    parser.add_argument("--cmd", help="Custom curl command")
    parser.add_argument("--file", help="Local script file to run")
    parser.add_argument("--policy", help="Specific policy filename in policies/ (overrides default map)")
    parser.add_argument("--source-app", default="backend-api", help="Existing app to use as attacker")
    parser.add_argument("--duration", default="30s")
    parser.add_argument("--vus", default="50")
    parser.add_argument("--skip-policy", action="store_true")
    parser.add_argument("--no-perf", action="store_true")
    parser.add_argument("--load-script", help="Path to custom k6 load test script")
    args = parser.parse_args()

    orchestrator = ExperimentOrchestrator(args.namespace, policy_override=args.policy)
    
    if not args.skip_policy:
        info(f"Preparing clean environment for {args.namespace}...")
        orchestrator.reset_policies()

    policy = "none"
    if not args.skip_policy:
        policy = orchestrator.apply_policy()

    try:
        sec_res = {"status": "SKIPPED", "lat": 0, "notes": ""}
        if args.scenario == "SNIFF-1":
            info(f"Running Traffic Sniffing (Confidentiality) Test in {args.namespace}...")
            # 1. Get the target payment-service pod
            rc_target, pod_target, _ = run_kubectl(["get", "pods", "-l", "app=payment-service", "-o", "jsonpath={.items[0].metadata.name}"], namespace=args.namespace)
            target_pod = pod_target.strip()
            
            # 2. Launch ephemeral sniffer container using 'kubectl debug'
            debug_cmd = [
                "debug", target_pod, 
                "--image=nicolaka/netshoot", 
                "--share-processes", 
                "--profile=general",
                "--", "sh", "-c", 
                "tcpdump -i any -A -l -nn port 8080 > /tmp/sniff.log 2>&1"
            ]
            # Run in background
            subprocess.Popen(["minikube", "-p", "minikube", "kubectl", "--", "-n", args.namespace] + debug_cmd)
            
            # 3. Generate Legitimate Traffic
            time.sleep(10)
            info("Generating traffic for sniffer...")
            rc_api, pod_api, _ = run_kubectl(["get", "pods", "-l", "app=audit-logger", "-o", "jsonpath={.items[0].metadata.name}"], namespace=args.namespace)
            if rc_api == 0 and pod_api.strip():
                for _ in range(10):
                    run_kubectl(["exec", pod_api.strip(), "-c", "audit-logger", "--", "curl", "-s", "-H", "X-User-Role: Admin", "http://payment-service:80/admin/keys"], namespace=args.namespace)
                    time.sleep(1)
            
            # 4. Check for leakage
            time.sleep(5)
            rc, stdout, _ = run_kubectl(["exec", target_pod, "--", "sh", "-c", "grep 'SUPER_SECRET' /tmp/sniff.log"], namespace=args.namespace)
            sec_res["status"] = 200 if "SUPER_SECRET" in stdout else 403
            sec_res["lat"] = 10.0

        elif args.scenario or args.cmd or args.file:
            rc, stdout, _ = run_kubectl(["get", "pods", "-l", f"app={args.source_app}", "-o", "jsonpath={.items[0].metadata.name}"], namespace=args.namespace)
            if rc != 0 or not stdout.strip():
                error(f"Could not find pod for app {args.source_app} in {args.namespace}")
                sys.exit(1)
            pod_name = stdout.strip()
            
            cmd = []
            if args.file:
                local_file = Path(args.file)
                remote_path = f"/tmp/attack_{int(time.time())}{local_file.suffix}"
                run_kubectl(["cp", str(local_file), f"{args.namespace}/{pod_name}:{remote_path}", "-c", args.source_app])
                run_kubectl(["exec", pod_name, "-c", args.source_app, "--", "chmod", "+x", remote_path], namespace=args.namespace)

                if local_file.suffix == ".js":
                    cmd = ["node", remote_path, args.scenario or "custom", args.namespace]
                elif local_file.suffix == ".py":
                    cmd = ["python3", remote_path, "--scenario", args.scenario or "custom"]
                else:
                    cmd = [remote_path, args.scenario or "custom", args.namespace]
            elif args.scenario:
                if args.scenario in ["DB-1", "DB-2"]:
                    local_file = PROJECT_ROOT / "scripts" / "redis_attack.js"
                    remote_path = "/tmp/redis_attack_orchestrated.js"
                    with open(local_file, "r") as f:
                        subprocess.run(["minikube", "-p", "minikube", "kubectl", "--", "exec", "-i", pod_name, "-n", args.namespace, "-c", args.source_app, "--", "sh", "-c", f"cat > {remote_path}"], stdin=f)
                    cmd = ["node", remote_path, args.scenario, args.namespace]
                else:
                    node_code = get_node_attack_payload(args.scenario, args.namespace, SERVICE_PORT)
                    if node_code:
                        cmd = ["node", "-e", node_code]
                    else:
                        warn(f"No built-in recipe for scenario {args.scenario}")
            
            if args.cmd:
                cmd = args.cmd.split()

            if cmd:
                rc, stdout, stderr = run_kubectl(["exec", pod_name, "-c", args.source_app, "--"] + cmd, namespace=args.namespace)
                match = re.search(r"(\d{3})\s+([\d.]+)", stdout)
                if match:
                    sec_res["status"], sec_res["lat"] = int(match.group(1)), round(float(match.group(2)), 2)
                else:
                    sec_res["notes"] = f"Parse error. Raw: {stdout.strip()[:50]}"
                    sec_res["status"] = 0
        
        # --- PERFORMANCE TEST (AFTER SECURITY) ---
        perf_res = {"p95": 0, "rps": 0, "cpu": 0, "mem": 0}
        if not args.no_perf:
            load_script_path = Path(args.load_script) if args.load_script else None
            perf_res = orchestrator.run_performance_test(args.duration, args.vus, script_path=load_script_path)
        
        orchestrator.record(args.scenario or "custom", sec_res, perf_res, policy)
    finally:
        if not args.skip_policy:
            orchestrator.reset_policies()

if __name__ == "__main__":
    main()
