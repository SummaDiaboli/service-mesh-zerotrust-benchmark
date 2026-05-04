import csv
from collections import Counter

def get_mode(data):
    if not data: return "N/A"
    return Counter(data).most_common(1)[0][0]

def get_mean(data):
    if not data: return 0.0
    return round(sum(data) / len(data), 2)

results = {}

with open("results/master_research_dataset.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ns = row["namespace"]
        pol = row["policy_applied"]
        
        if ns == "ns-baseline":
            env = "Baseline"
        elif "istio" in ns:
            env = "Istio-With-Policy" if pol != "none" else "Istio-No-Policy"
        elif "linkerd" in ns:
            env = "Linkerd-With-Policy" if pol != "none" else "Linkerd-No-Policy"
        else:
            env = ns
            
        key = (env, row["scenario"])
        if key not in results:
            results[key] = {
                "results": [], "statuses": [], "latencies": [],
                "p95": [], "rps": [], "cpu": [], "mem": []
            }
        
        results[key]["results"].append(row["attack_result"])
        results[key]["statuses"].append(row["http_status"])
        results[key]["latencies"].append(float(row["latency_ms"] or 0))
        results[key]["p95"].append(float(row["p95_latency_ms"] or 0))
        results[key]["rps"].append(float(row["rps"] or 0))
        results[key]["cpu"].append(float(row["avg_cpu_m"] or 0))
        results[key]["mem"].append(float(row["avg_memory_mi"] or 0))

# Compile statistical report
final_report = []
for (env, sc), data in results.items():
    final_report.append({
        "environment": env,
        "scenario": sc,
        "mode_result": get_mode(data["results"]),
        "mode_status": get_mode(data["statuses"]),
        "avg_lat": get_mean(data["latencies"]),
        "avg_p95": get_mean(data["p95"]),
        "avg_rps": get_mean(data["rps"]),
        "avg_cpu": get_mean(data["cpu"]),
        "avg_mem": get_mean(data["mem"])
    })

# Sort by Scenario then Environment
final_report.sort(key=lambda x: (x["scenario"], x["environment"]))

print(f"{'SCENARIO':<15} {'ENVIRONMENT':<20} {'RESULT':<12} {'STATUS':<8} {'p95':<10} {'RPS':<10} {'CPU':<8} {'MEM':<8}")
print("-" * 105)
for r in final_report:
    print(f"{r['scenario']:<15} {r['environment']:<20} {r['mode_result']:<12} {r['mode_status']:<8} {r['avg_p95']:<10} {r['avg_rps']:<10} {r['avg_cpu']:<8} {r['avg_mem']:<8}")

# Save to CSV for future use
with open("results/scenario_statistical_analysis.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=final_report[0].keys())
    writer.writeheader()
    writer.writerows(final_report)
