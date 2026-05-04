import csv


def memory_grouped_bar_chart():
    values = [27.66, 129.05, 119.14, 120.20, 129.38]
    colors = ["#4a90e2", "#e8a0a8", "#d0021b", "#b8e08a", "#7ed321"]
    max_v, cw, ch = 250.0, 360, 165
    ml, mr, mt, mb = 46, 15, 15, 45
    pw, ph = cw - ml - mr, ch - mt - mb   # 299, 105
    yb = mt + ph                           # 120
    bw, bg, gg, pad = 44, 6, 22, 6
    # left edge of each bar
    x0 = ml + pad
    x1 = x0 + bw + gg
    x2 = x1 + bw + bg
    x3 = x2 + bw + gg
    x4 = x3 + bw + bg
    xp = [x0, x1, x2, x3, x4]
    hp = [ph * v / max_v for v in values]
    yt = [yb - h for h in hp]
    gw = bw + bg + bw   # Istio/Linkerd group label width = 94

    L = []
    L.append('#figure(')
    L.append('  caption: [Global average memory consumption (MiB) across the five experimental environments. Linkerd-With-Policy (129.38 MiB) exceeded Istio-With-Policy (119.14 MiB), inverting the expected lightweight trade-off.],')
    L.append(')[')
    L.append('#block(width: 100%, stroke: 0.5pt + gray, inset: 10pt, radius: 4pt, breakable: false)[')
    L.append('  *Global Average Memory Consumption (MiB)* \\')
    L.append('  #v(5pt)')
    L.append('  #align(center)[')
    L.append(f'    #block(width: {cw}pt, height: {ch}pt)[')
    L.append(f'      #place(dx: {ml}pt, dy: {mt}pt, line(start: (0pt, 0pt), end: (0pt, {ph}pt), stroke: 0.5pt + luma(150)))')
    L.append(f'      #place(dx: {ml}pt, dy: {yb}pt, line(start: (0pt, 0pt), end: ({pw}pt, 0pt), stroke: 0.5pt + luma(150)))')
    for v in [0, 50, 100, 150, 200, 250]:
        gy = mt + ph * (1.0 - v / max_v)
        L.append(f'      #place(dx: {ml}pt, dy: {gy:.1f}pt, line(start: (0pt, 0pt), end: ({pw}pt, 0pt), stroke: 0.3pt + luma(215)))')
        L.append(f'      #place(dx: 0pt, dy: {gy - 5:.1f}pt, box(width: {ml - 4}pt)[#align(right)[#text(size: 7pt)[{v}]]])')
    for i in range(5):
        L.append(f'      #place(dx: {xp[i]:.1f}pt, dy: {yt[i]:.1f}pt, rect(width: {bw}pt, height: {hp[i]:.1f}pt, fill: rgb("{colors[i]}"), stroke: none))')
        L.append(f'      #place(dx: {xp[i]:.1f}pt, dy: {yt[i] - 12:.1f}pt, box(width: {bw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[{values[i]}]]])')
    ly1, ly2 = yb + 6, yb + 15
    L.append(f'      #place(dx: {x0}pt, dy: {ly1}pt, box(width: {bw}pt)[#align(center)[#text(size: 6.5pt)[Baseline]]])')
    L.append(f'      #place(dx: {x1}pt, dy: {ly1}pt, box(width: {gw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[Istio]]])')
    L.append(f'      #place(dx: {x1}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[No Pol]]])')
    L.append(f'      #place(dx: {x2}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[With Pol]]])')
    L.append(f'      #place(dx: {x3}pt, dy: {ly1}pt, box(width: {gw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[Linkerd]]])')
    L.append(f'      #place(dx: {x3}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[No Pol]]])')
    L.append(f'      #place(dx: {x4}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[With Pol]]])')
    L.append('    ]')
    L.append('  ]')
    L.append(']')
    L.append(']')
    return '\n'.join(L) + '\n'


def security_outcome_matrix():
    cats = [
        ("Application Layer Authorization", [
            ("HTTP-1", "Path Exposure",        True,  True),
            ("HTTP-2", "Method Violation",     True,  True),
            ("HTTP-3", "Header Spoofing",      True,  True),
            ("HTTP-4", "CORS Violation",       True,  True),
            ("JWT-1",  "JWT Validation",       True,  True),
        ]),
        ("Identity and Network Security", [
            ("IP-1",   "IP Spoofing",          True,  True),
        ]),
        ("Binary Protocols and Database Security", [
            ("RPC-1",  "gRPC Method Abuse",    True,  True),
            ("DB-1",   "Redis Sniffing Bypass",False, False),
        ]),
        ("Protocol Evasion and Downgrade", [
            ("DG-1",     "Port-Protocol Mismatch", True,  False),
            ("DG-2",     "Protocol Bypass",        True,  False),
        ]),
        ("Resilience and Availability", [
            ("EX-2",       "HTTP Flood",        True,  True),
            ("EX-3",       "Slowloris",         True,  True),
            ("Avail-Storm","Volumetric Storm",   True,  True),
        ]),
        ("Egress and Chained Attacks", [
            ("EX-1",       "Egress Exfiltration", True,  False),
            ("Exfil-Chain","Attack Chain",         True,  True),
        ]),
        ("Network Drops vs. Deep Packet Inspection", [
            ("Combined-HTTP","Multi-Path Evasion",    True,  False),
            ("Full-Comp",    "Complete Compromise",   False, False),
        ]),
    ]
    gf = 'rgb("#d5f5e3")'
    rf = 'rgb("#fadbd8")'

    def cell(blocked):
        return f'table.cell(fill: {gf if blocked else rf})[#text(size: 8pt)[{"BLOCKED" if blocked else "VULN"}]]'

    L = []
    L.append('#figure(')
    L.append('  caption: [Security outcome matrix. Baseline is vulnerable in all 17 scenarios, as expected. Istio blocks 15 of 17; Linkerd blocks 11 of 17 under correctly configured active policies.],')
    L.append(')[')
    L.append('  #table(')
    L.append('    columns: (2fr, 1.1fr, 1.1fr, 1.1fr),')
    L.append('    inset: (x: 6pt, y: 4pt),')
    L.append('    align: (left, center, center, center),')
    L.append('    [*Scenario*], [*Baseline*], [*Istio*], [*Linkerd*],')
    for cat, rows in cats:
        L.append(f'    table.cell(colspan: 4, fill: luma(230))[#text(size: 8pt, weight: "bold")[{cat}]],')
        for sid, name, istio, linkerd in rows:
            L.append(f'    [#text(size: 8pt)[`{sid}` -- {name}]], {cell(False)}, {cell(istio)}, {cell(linkerd)},')
    L.append('  )')
    L.append(']')
    return '\n'.join(L) + '\n'


def ex2_before_after_chart():
    # p95 latency (ms) from scenario_statistical_analysis.csv
    values = [187.91, 153.96, 9.59, 6.64]
    colors = ["#d0021b", "#7ed321", "#d0021b", "#7ed321"]
    max_ms, cw, ch = 220.0, 320, 160
    ml, mr, mt, mb = 45, 10, 25, 45
    pw, ph = cw - ml - mr, ch - mt - mb   # 265, 90
    yb = mt + ph                           # 115
    bw, bg, gg, pad = 45, 8, 45, 10
    xp = [
        ml + pad,
        ml + pad + bw + bg,
        ml + pad + bw + bg + bw + gg,
        ml + pad + bw + bg + bw + gg + bw + bg,
    ]
    hp = [ph * v / max_ms for v in values]
    yt = [yb - h for h in hp]
    gw = bw + bg + bw   # group label width = 98

    L = []
    L.append('#figure(')
    L.append('  caption: [EX-2 p95 latency (ms) before and after rate-limiting policy. Istio: 187.91ms → 9.59ms; Linkerd: 153.96ms → 6.64ms. Both reductions are direct expressions of the Efficiency of Rejection.],')
    L.append(')[')
    L.append('#block(width: 100%, stroke: 0.5pt + gray, inset: 10pt, radius: 4pt, breakable: false)[')
    L.append('  *EX-2: p95 Latency Before and After Rate Limiting Policy (ms)* \\')
    L.append('  #v(5pt)')
    L.append('  #align(center)[')
    L.append(f'    #block(width: {cw}pt, height: {ch}pt)[')
    L.append(f'      #place(dx: {ml}pt, dy: {mt}pt, line(start: (0pt, 0pt), end: (0pt, {ph}pt), stroke: 0.5pt + luma(150)))')
    L.append(f'      #place(dx: {ml}pt, dy: {yb}pt, line(start: (0pt, 0pt), end: ({pw}pt, 0pt), stroke: 0.5pt + luma(150)))')
    for v in [0, 50, 100, 150, 200]:
        gy = mt + ph * (1.0 - v / max_ms)
        L.append(f'      #place(dx: {ml}pt, dy: {gy:.1f}pt, line(start: (0pt, 0pt), end: ({pw}pt, 0pt), stroke: 0.3pt + luma(215)))')
        L.append(f'      #place(dx: 0pt, dy: {gy - 5:.1f}pt, box(width: {ml - 4}pt)[#align(right)[#text(size: 7pt)[{v}]]])')
    for i in range(4):
        L.append(f'      #place(dx: {xp[i]:.1f}pt, dy: {yt[i]:.1f}pt, rect(width: {bw}pt, height: {hp[i]:.1f}pt, fill: rgb("{colors[i]}"), stroke: none))')
        L.append(f'      #place(dx: {xp[i]:.1f}pt, dy: {yt[i] - 12:.1f}pt, box(width: {bw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[{values[i]}]]])')
    ly1, ly2 = yb + 6, yb + 15
    L.append(f'      #place(dx: {xp[0]:.1f}pt, dy: {ly1}pt, box(width: {gw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[No Policy]]])')
    L.append(f'      #place(dx: {xp[0]:.1f}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[Istio]]])')
    L.append(f'      #place(dx: {xp[1]:.1f}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[Linkerd]]])')
    L.append(f'      #place(dx: {xp[2]:.1f}pt, dy: {ly1}pt, box(width: {gw}pt)[#align(center)[#text(size: 6.5pt, weight: "bold")[With Policy]]])')
    L.append(f'      #place(dx: {xp[2]:.1f}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[Istio]]])')
    L.append(f'      #place(dx: {xp[3]:.1f}pt, dy: {ly2}pt, box(width: {bw}pt)[#align(center)[#text(size: 6pt)[Linkerd]]])')
    L.append('    ]')
    L.append('  ]')
    L.append(']')
    L.append(']')
    return '\n'.join(L) + '\n'


def generate():
    scenarios_meta = {
        "HTTP-1": ("Path Exposure", "Targeting exfiltration of secrets from `/api/internal/secrets`."),
        "HTTP-2": ("Method Violation", "Testing restriction of `DELETE` verb on append-only endpoints."),
        "HTTP-3": ("Header Spoofing", "Injecting `X-User-Role: Admin` to bypass application logic."),
        "HTTP-4": ("CORS Violation", "Attempting unauthorized cross-origin requests from `evil.com`."),
        "RPC-1":  ("gRPC Method Abuse", "Targeting unauthorized refunds via `/payment.Service/Refund`."),
        "DB-1":   ("Redis Sniffing Bypass", "Using raw TCP sockets to blind L7 database filters."),
        "IP-1":   ("Identity vs IP Spoofing", "Spoofing `X-Forwarded-For` to bypass IP-based ACLs."),
        "EX-1":   ("Egress Exfiltration", "Attempting to send data to unauthorized external domain `google.com`."),
        "EX-2":   ("HTTP Flood", "Volumetric request burst to test rate-limiting efficacy."),
        "EX-3":   ("Slowloris", "Connection exhaustion attack testing proxy timeout enforcement."),
        "JWT-1":  ("JWT Validation", "Testing cryptographic signature verification at the mesh edge."),
        "DG-1":   ("Port-Protocol Mismatch", "Sending HTTP traffic to a port explicitly named `grpc`."),
        "DG-2": ("Protocol Bypass", "Using raw ASCII bytes via TCP to hide HTTP traffic from parsers."),
        "Combined-HTTP": ("Multi-Path Evasion", "Simultaneous multi-vector L7 evasion techniques."),
        "Exfil-Chain": ("Attack Chain", "Chained data read and subsequent egress exfiltration."),
        "Avail-Storm": ("Volumetric Storm", "Massive multi-pod volumetric flood to test stability."),
        "Full-Comp": ("Complete Compromise", "Measuring rejection efficiency during catastrophic system failure.")
    }

    categories = [
        ("Application Layer Authorization", ["HTTP-1", "HTTP-2", "HTTP-3", "HTTP-4", "JWT-1"]),
        ("Identity and Network Security", ["IP-1"]),
        ("Binary Protocols and Database Security", ["RPC-1", "DB-1"]),
        ("Protocol Evasion and Downgrade", ["DG-1", "DG-2"]),
        ("Resilience and Availability", ["EX-2", "EX-3", "Avail-Storm"]),
        ("Egress and Chained Attacks", ["EX-1", "Exfil-Chain"]),
        ("Network Drops vs. Deep Packet Inspection", ["Combined-HTTP", "Full-Comp"])
    ]

    data = {}
    with open("results/scenario_statistical_analysis.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sc = row["scenario"]
            if sc == "DG-2-Std": sc = "DG-2"
            env = row["environment"]
            if sc not in data: data[sc] = {}
            data[sc][env] = row

    typ_code = """#set heading(numbering: "1.1")

#let comparison_graph(label, baseline, istio_no, istio_with, linkerd_no, linkerd_with, unit, max_val) = {
  block(width: 100%, stroke: 0.5pt + gray, inset: 10pt, radius: 4pt, breakable: false)[
    *#label (#unit)* \\
    #v(5pt)
    #let scale = 100% / max_val
    #grid(
      columns: (120pt, 1fr),
      column-gutter: 8pt,
      row-gutter: 8pt,
      align: horizon,
      [Baseline], stack(dir: ltr, rect(width: baseline * scale, height: 8pt, fill: rgb("#4a90e2")), h(4pt), text(size: 7pt)[#baseline]),
      [Istio (No Pol)], stack(dir: ltr, rect(width: istio_no * scale, height: 8pt, fill: rgb("#d0021b").lighten(40%)), h(4pt), text(size: 7pt)[#istio_no]),
      [Istio (With Pol)], stack(dir: ltr, rect(width: istio_with * scale, height: 8pt, fill: rgb("#d0021b")), h(4pt), text(size: 7pt)[#istio_with]),
      [Linkerd (No Pol)], stack(dir: ltr, rect(width: linkerd_no * scale, height: 8pt, fill: rgb("#7ed321").lighten(40%)), h(4pt), text(size: 7pt)[#linkerd_no]),
      [Linkerd (With Pol)], stack(dir: ltr, rect(width: linkerd_with * scale, height: 8pt, fill: rgb("#7ed321")), h(4pt), text(size: 7pt)[#linkerd_with]),
    )
  ]
}

= Results and Discussion

This chapter presents the comprehensive findings from the batch execution cycles, evaluating security efficacy and performance metrics across Baseline, Istio, and Linkerd environments.

""" + security_outcome_matrix() + """

== Granular Scenario Analysis

This section presents the per-scenario experimental results across all 17 attack vectors, grouped by threat category. Each scenario reports the security outcome (BLOCKED or VULNERABLE) and the key performance metrics (p95 latency and average throughput) for all five experimental environments: Baseline, Istio without policy, Istio with policy, Linkerd without policy, and Linkerd with policy. A CPU overhead bar chart accompanies each scenario to show resource consumption changes under policy enforcement.

The results tables should be read with two comparisons in mind. The vertical comparison between No-Policy and With-Policy states within the same mesh isolates the performance cost attributable directly to the active authorization rule. The horizontal comparison between Istio and Linkerd under equivalent policy reveals the architectural trade-offs between Envoy's composite filter chain and Linkerd's per-route evaluation model. Scenarios where the policy is applied but the attack is not blocked are as analytically significant as successful blocks, since they identify the enforcement layer mismatches and protocol blind spots that define each mesh's practical coverage boundary.
"""

    for cat_name, sids in categories:
        typ_code += f"\n=== {cat_name}\n"
        for sid in sids:
            if sid not in data: continue
            name, desc = scenarios_meta[sid]
            envs = data[sid]
            
            typ_code += "\n==== " + sid + ": " + name + "\n" + desc + "\n\n"
            typ_code += f"#figure(\n  caption: [Security results for {sid}: {name}.],\n)[\n"
            typ_code += "#table(\n  columns: (1.5fr, 1.3fr, 0.6fr, 1fr, 0.7fr),\n  inset: 6pt,\n  [*Environment*], [*Result*], [*Status*], [*p95 Latency*], [*Avg RPS*],\n"

            target_envs = ["Baseline", "Istio-No-Policy", "Istio-With-Policy", "Linkerd-No-Policy", "Linkerd-With-Policy"]
            for te in target_envs:
                r = envs[te]
                typ_code += f"  [{te}], [{r['mode_result']}], [{r['mode_status']}], [{r['avg_p95']}ms], [{r['avg_rps']}],\n"
            typ_code += ")\n]\n\n"
            
            max_cpu = 700.0
            typ_code += '#comparison_graph("' + sid + ' CPU Overhead", ' + envs["Baseline"]["avg_cpu"] + ', ' + envs["Istio-No-Policy"]["avg_cpu"] + ', ' + envs["Istio-With-Policy"]["avg_cpu"] + ', ' + envs["Linkerd-No-Policy"]["avg_cpu"] + ', ' + envs["Linkerd-With-Policy"]["avg_cpu"] + ', "m", ' + str(max_cpu) + ')\n\n'
            
            typ_code += "\n"
            if sid == "HTTP-1":
                typ_code += "Both meshes successfully blocked unauthorized access to `/api/internal/secrets` under active L7 policy, confirming that path-based authorization is a well-supported primitive in both Istio and Linkerd. The more operationally significant finding lies in how each mesh communicates rejection. Istio returned a clean HTTP `403` across all three runs, giving client applications an unambiguous, actionable error code. Linkerd, by contrast, issued a TCP-level reset in all three policy-enforced runs, recorded as `Status 0`.\n\nThis is an L4-level rejection: rather than completing the HTTP handshake to return a structured error response, the proxy closed the connection at the transport layer. This behaviour is consistent with Linkerd's layered security model, where a path-based restriction that does not match any authorized `HTTPRoute` causes the `Server` policy to terminate the connection before L7 parsing is attempted. A consuming service receiving `Status 0` cannot distinguish a policy block from a network failure or a crashed upstream, which has meaningful implications for observability, alerting, and circuit-breaker logic in production environments.\n\nThe resource consumption pattern across both meshes is consistent with the *Efficiency of Rejection*. Istio's CPU decreased from approximately 273m to 242m under active policy, and Linkerd's from approximately 253m to 243m. By terminating requests at the path-check stage before upstream proxying and response assembly are performed, the sidecar avoids the higher-cost operations that unconditional forwarding would otherwise incur. Notably, Linkerd's p95 latency increased from approximately 129ms to 190ms under policy enforcement — a 61ms *Instrumentation Tax* attributable to the overhead of activating the `HTTPRoute` path-matching filter chain on every inbound request, even those that are immediately rejected.\n"
            elif sid == "HTTP-2":
                typ_code += "Both meshes successfully prevented unauthorized use of the `DELETE` verb on the append-only logging endpoint under active L7 policy. In contrast to HTTP-1, Linkerd returned a proper `404` rather than a TCP-level reset, confirming that the `HTTPRoute` engine engaged and completed L7 parsing before issuing the rejection. This is the expected behaviour when a request reaches the L7 layer but does not match any permitted method: Linkerd processes the request through its route-matching logic and responds at the protocol level rather than terminating the connection at the transport layer. However, `404` is semantically imprecise for a method violation. It signals that the resource does not exist rather than that the requested method is prohibited. The correct response for this scenario is `405` Method Not Allowed. In production environments where downstream services perform error-code-driven routing or alerting, this distinction matters for accurate failure classification. Beyond the binary security outcome, the resource consumption pattern here is noteworthy: CPU utilization decreased when policies were enforced in both meshes, from approximately 326m to 234m in Istio, and from 288m to 200m in Linkerd. By terminating the request at the method-check stage in the proxy, the sidecar avoids the higher-cost operations of upstream connection management and response streaming, yielding a net reduction in compute even at normal traffic volumes. This is an early manifestation of the Efficiency of Rejection outside of a volumetric context.\n"
            elif sid == "HTTP-3":
                typ_code += "Both meshes successfully blocked the injection of unauthorized `X-User-Role: Admin` headers under active L7 policy, confirming that header-level authorization is enforceable at the proxy layer before any payload reaches the application. This is architecturally significant: application services commonly trust internal headers by default, meaning that without proxy-level interception, a compromised pod can trivially escalate privileges by crafting headers the application was never designed to validate independently. The performance patterns across the two meshes diverge in a way that directly illustrates the competing forces of the Instrumentation Tax and the Efficiency of Rejection. In Istio, enforcing the header policy produced a slight reduction in p95 latency and a corresponding increase in throughput compared to the permissive state. Early termination at the header inspection stage is computationally cheaper than completing the upstream proxy cycle, so the policy pays for itself even at normal traffic volumes. In Linkerd, the inverse occurred: latency increased from approximately 132ms to 157ms with policy applied while throughput remained essentially unchanged. Here the attack volume is insufficient to generate meaningful rejection savings, so the fixed cost of traversing the newly activated authorization filter chain manifests as a net overhead. This is the Instrumentation Tax operating without the offsetting effect of high-volume rejection. Linkerd again returned `404` as the rejection code, consistent with the L7 engagement pattern observed in HTTP-2, where the `HTTPRoute` engine completed parsing before responding. As with HTTP-2, the semantically correct response for a header-based authorization failure would be `403` Forbidden, since the resource exists and the method is valid but the request lacks the required authorization attributes.\n"
            elif sid == "HTTP-4":
                typ_code += "Both meshes successfully blocked cross-origin requests originating from an unauthorized domain under active L7 policy, confirming that origin-based access control is enforceable at the sidecar layer before any application logic is reached. This is particularly relevant in microservice environments where CORS validation is commonly delegated to individual services, creating inconsistency risk when new services are introduced without inheriting the same application-level controls. Linkerd's performance profile here produces the most pronounced Efficiency of Rejection signal observed across the application layer scenarios. With policy enforced, p95 latency decreased from approximately 131ms to 107ms while throughput remained essentially unchanged. The proxy's early rejection of requests from unauthorized origins avoids the cost of upstream connection establishment and response proxying, producing a latency improvement even in the absence of volumetric attack load. This reinforces that the efficiency gain from early termination is not exclusive to flood scenarios but is observable whenever the rejected request would otherwise require meaningful upstream processing. Notably, Linkerd returned `403` as the rejection code in this scenario, in contrast to the `404` responses observed in HTTP-2 and HTTP-3. This is the first semantically correct rejection code from Linkerd across the application layer scenarios, and it suggests that CORS origin validation exercises a distinct enforcement path within the proxy compared to route and method matching. Whether this reflects an intentional distinction in how Linkerd's `HTTPRoute` policy handles origin-based rules versus path and method rules warrants attention in any production deployment where consistent, predictable error codes are required across policy types.\n"
            elif sid == "RPC-1":
                typ_code += "Both meshes successfully blocked unauthorized invocation of the `/payment.Service/Refund` gRPC method under active L7 policy, confirming that binary protocol enforcement at the method level is achievable within the sidecar model. However, a critical architectural disparity emerged in how each mesh defines its enforcement boundary. Istio intercepted intra-pod loopback traffic directed at the service's own IP address, demonstrating that its Envoy-based sidecar operates at the container level. All traffic, including calls that originate and terminate within the same pod, is routed through the proxy and subject to policy evaluation. Linkerd, by contrast, did not intercept loopback traffic of this kind, indicating that its enforcement boundary operates at the pod level rather than the container level. Traffic that does not cross the pod network boundary is outside the reach of Linkerd's proxy. The security implication of this distinction is concrete. An attacker who has compromised a container within a multi-container pod can potentially communicate with co-located services without traversing Linkerd's enforcement layer, since the traffic never enters the pod network namespace where the proxy intercepts it. Under Istio, the same attacker would still have their traffic inspected and subject to policy, as the sidecar intercepts at the container boundary regardless of traffic origin. In environments running multi-container pod architectures, this difference represents a structural gap in Linkerd's Zero Trust coverage that L7 policies alone cannot close. Both meshes returned clean HTTP `403` responses across all three runs, and CPU consumption decreased under active enforcement in both cases, consistent with the Efficiency of Rejection pattern observed throughout the application layer scenarios.\n"
            elif sid == "DB-1":
                typ_code += "Both meshes were successfully bypassed by raw TCP socket communication using the Redis RESP protocol, and critically, this outcome was identical regardless of whether a policy was applied. The performance metrics across the No-Policy and With-Policy states are virtually indistinguishable in both meshes, which is itself significant: it confirms that the policy was never engaged rather than engaged and defeated. The proxy had no L7 visibility into the traffic stream to enforce against. The root cause is architectural rather than configurational. Service mesh sidecars are optimised for `HTTP/1.1`, `HTTP/2`, and `gRPC`. When a proxy encounters a protocol it cannot parse, it defaults to opaque TCP mode, forwarding the byte stream without inspection. In this scenario, the `RESP` protocol bytes were not recognised as a known application protocol, causing both proxies to treat the connection as raw TCP and bypass their L7 filter chains entirely. No policy revision or additional rule complexity could change this outcome, because the enforcement layer that policies operate on was never reached. This establishes a hard boundary on what L7 authorization policies can protect. Non-HTTP backend protocols, including databases, message queues, and any service using a binary or proprietary wire format, are outside the inspection capability of both meshes in their default configurations. The appropriate remediation is not a mesh policy but a complementary set of controls: L4 network policies restricting which workloads can initiate connections to the Redis port, native Redis authentication and access control lists, and where possible, a protocol gateway that terminates the Redis connection and re-exposes it over an HTTP-inspectable interface. L7 security via service mesh must be understood as a partial control that requires underpinning by L4 identity enforcement for non-HTTP workloads.\n"
            elif sid == "DG-2":
                typ_code += "Istio successfully blocked the attempt to disguise HTTP traffic as raw ASCII bytes sent over a TCP stream, while Linkerd remained vulnerable across all three runs. The attack exploits a specific weakness in protocol detection logic: by stripping standard HTTP framing and sending the request as raw ASCII, the attacker attempts to prevent the proxy from identifying the stream as HTTP and engaging its L7 filter chain. Istio's Envoy-based proxy performs deep protocol inspection that is resilient to this technique, identifying the underlying HTTP semantics in the byte stream and applying the active policy accordingly. Linkerd's proxy, optimised for throughput and minimal parsing overhead, does not perform the same depth of inspection, allowing the disguised traffic to pass without policy evaluation. As observed in DG-1, Linkerd's CPU consumption decreased under active policy enforcement from approximately 303m to 241m despite the attack succeeding. The policy was applied and influenced proxy processing without producing a security outcome, again confirming that the enforcement layer the policy targets was not reached. Istio exhibited the largest Efficiency of Rejection signal observed across the protocol evasion scenarios, with CPU dropping from approximately 410m to 286m under active policy. The depth of Envoy's protocol inspection, which enables it to catch disguised traffic that Linkerd misses, does not come at a sustained compute cost once enforcement is active. Early rejection of non-conforming streams at the inspection stage is computationally cheaper than completing the upstream proxy cycle for traffic that would ultimately be blocked. During the transition between experimental states in this scenario, *Ghost Connection* behaviour was also observed, where persistent TCP connections established during the permissive phase continued to bypass newly applied policies until an active connection flush was performed. This finding is addressed in full in Section 5.2.\n"
            elif sid == "IP-1":
                typ_code += "Both meshes successfully blocked the attempt to spoof a trusted local IP address via `X-Forwarded-For` header manipulation, but the reason for this success is more architecturally significant than the binary outcome suggests. IP-based access control in traditional network security is fundamentally vulnerable to header manipulation because IP addresses are mutable, spoofable, and meaningless as identity primitives in environments where traffic traverses multiple proxies and load balancers. The reason this attack fails under service mesh enforcement is not simply that a policy matched a header value, but that the mesh's authorization model is grounded in cryptographic workload identity established at the mTLS handshake. The `X-Forwarded-For` header is application-layer metadata that an attacker can freely craft; the mTLS certificate presented at connection time is not. By anchoring authorization decisions to the latter rather than the former, both meshes implement the Zero Trust principle of never trusting network location as a proxy for identity. Both Istio and Linkerd returned clean HTTP `403` responses across all three runs, a consistency that is worth noting against the backdrop of the application layer scenarios where Linkerd produced TCP resets and semantically imprecise `404` codes depending on the policy type exercised. Identity-based enforcement via mTLS appears to engage a more uniform rejection path in Linkerd than route or method-based `HTTPRoute` policies. CPU consumption decreased under active policy enforcement in both meshes, consistent with the Efficiency of Rejection pattern observed across the preceding scenarios. The connection is terminated at the identity verification stage before any upstream processing occurs, yielding a compute saving that compounds the security benefit of cryptographic enforcement.\n"
            elif sid == "EX-1":
                typ_code += "Istio successfully blocked the attempt to send sensitive data to an unauthorized external domain under active L7 policy, while Linkerd remained vulnerable across all three runs. The HTTP `301` status recorded in Linkerd's With-Policy state is worth examining precisely: a `301` is not an ambiguous connection error or a timeout. It is a redirect response returned by the external destination, meaning the exfiltration request completed a full round trip out of the cluster and received a response from `google.com`. The policy was applied and the proxy was active, but the data left the cluster regardless. This is confirmed exfiltration, not a marginal policy miss. The architectural reason for Linkerd's failure here is distinct from the protocol detection gaps observed in DB-1 and the evasion techniques in DG-1 and DG-2. Linkerd's proxy is designed to enforce policy on traffic flowing between meshed workloads within the cluster. Outbound traffic to external destinations is treated as opaque TCP by default, as the proxy has no mechanism to parse or match against external FQDNs at the L7 layer. No HTTPRoute policy primitive in Linkerd's model can block a specific external domain because the policy model does not extend to uninstrumented external endpoints. Closing this gap in a Linkerd environment requires a complementary egress gateway or CNI-level network policy that operates outside the mesh's enforcement boundary. Istio's egress control operates through its Envoy-based outbound filter chain, which applies L7 inspection to outbound traffic and can match against specific external hostnames defined in `ServiceEntry` resources. This capability is absent from Linkerd's architecture by design rather than by configuration oversight. Linkerd's CPU decreased from approximately 282m to 220m under active policy despite the attack succeeding, consistent with the pattern observed in scenarios where policy overhead is incurred without a security outcome. The policy influenced proxy processing without engaging the enforcement layer relevant to egress traffic.\n"
            elif sid == "EX-2":
                typ_code += "This scenario produced the most operationally striking data in the dataset and provides the clearest empirical illustration of the *Efficiency of Rejection* principle, with both meshes successfully blocking the volumetric flood attack under correctly configured active policy enforcement. Under Istio's active local rate limiter, p95 latency collapsed from approximately 188ms to 9.59ms while throughput increased from roughly 688 RPS to over 9,000 RPS. These figures are not a performance improvement in the conventional sense but a direct consequence of how the proxy handles volumetric rejection: a `429` response generated at the proxy edge requires no upstream connection, no application context switch, and no response body assembly. The sidecar terminates the request at the rate-limit check stage and returns a minimal fixed response, a computation that is orders of magnitude cheaper than proxying a legitimate request to the upstream service. The result is that the system under active attack with a policy enforced is measurably faster and more stable than the same system under attack without one. Linkerd's result requires contextual explanation regarding policy primitive selection. An initial experimental run using an `HTTPRoute` request timeout of 500ms produced no security outcome: a timeout-based approach is fundamentally insufficient to shed volumetric flood traffic because, while it terminates individual slow or long-running requests quickly, it does not limit the rate at which new connections are accepted. The flood continued to saturate the proxy and the No-Policy and With-Policy states produced virtually identical throughput and latency figures, with the policy overhead incurred but no `429` responses generated. The corrected experiment deployed Linkerd's native `HTTPLocalRateLimitPolicy` primitive, configured with a total cap of 100 RPS and a per-identity cap of 20 RPS anchored to a `Server` resource reference targeting the payment service port. This primitive operates at the connection acceptance layer rather than the request timeout layer, allowing the proxy to shed excess traffic before it enters the processing pipeline. Under this configuration, Linkerd successfully blocked the flood across all three runs, returning `429` responses and exhibiting the Efficiency of Rejection pattern with greater intensity than Istio. Linkerd's p95 latency under active enforcement was 6.64ms at 10,882 RPS, compared to Istio's 9.59ms at 9,025 RPS, a result that is consistent with Linkerd's throughput-optimised Rust-based proxy being computationally cheaper at the specific task of generating fixed rejection responses at high rate. The CPU comparison reinforces this: Linkerd drew approximately 150m under active enforcement against Istio's 346m, while Linkerd's No-Policy CPU was approximately 185m at 929 RPS. The reduction from 185m to 150m under active enforcement, while throughput simultaneously increased from 929 RPS to 10,882 RPS, is a direct expression of the *Efficiency of Rejection* pattern: the proxy sheds over 10,000 requests per second at the rate-limit edge, a computation cheap enough that aggregate CPU falls despite processing an order of magnitude more requests per second than in the unprotected state. The finding has a direct implication for the study's Linkerd scorecard and for practitioners: Linkerd is capable of volumetric flood defense equivalent to or exceeding Istio's in terms of latency and throughput, but only when the correct policy primitive is selected. The `HTTPLocalRateLimitPolicy` primitive is the appropriate mechanism; timeout-based `HTTPRoute` policies do not address this threat category. A final architectural distinction is worth recording for operators evaluating rate limiting granularity. Both the Istio and Linkerd configurations deployed in this scenario apply rate limits at the port level. Istio's `EnvoyFilter` patches the local rate limiter into the `SIDECAR_INBOUND` HTTP connection manager filter chain before the router, producing a blanket 10 RPS cap across all inbound paths to the payment service. Linkerd's `HTTPLocalRateLimitPolicy` targets a `Server` resource, which is inherently a port-level anchor, and applies its caps uniformly across all traffic reaching that port. The architecturally significant difference is in what each mesh can offer beyond this study's configuration. Istio can apply path-scoped rate limits by attaching per-route descriptors in a `VirtualService`, enabling operators to enforce different caps on sensitive paths such as `/admin/keys` versus high-volume operational paths such as `/process`. Linkerd's `HTTPLocalRateLimitPolicy` has no path-level counterpart in its policy API: the `Server` resource is the finest-grained anchor available, making port-level the floor for rate limiting granularity in Linkerd. For workloads requiring differentiated rate limiting by endpoint, this structural difference may influence mesh selection independent of the raw throughput characteristics observed here.\n" + ex2_before_after_chart()
            elif sid == "EX-3":
                typ_code += "Both meshes blocked the Slowloris attack in their No-Policy states, confirming that this protection is a property of the sidecar proxy architecture rather than the result of any explicitly configured L7 rule. The baseline Kubernetes environment, which lacks a sidecar layer, remained vulnerable across all three runs. This contrast is important: it demonstrates that deploying a service mesh provides a meaningful default security improvement over standard Kubernetes even before any policy is written, specifically through the proxy's built-in connection timeout management. Slowloris works by holding large numbers of partial HTTP connections open indefinitely to exhaust application thread pools. Sidecar proxies are designed to manage connection lifecycles aggressively, enforcing timeouts that cause incomplete connections to be terminated before they can accumulate to the point of service exhaustion. The CPU consumption pattern under Istio's With-Policy state diverges from the Efficiency of Rejection trend observed across preceding scenarios. Rather than decreasing under active enforcement, Istio's CPU increased from approximately 355m to 614m when a policy was applied on top of the inherent proxy timeout handling. This reflects the *Instrumentation Tax* operating in a scenario where the attack is already being neutralised by the proxy's default behaviour: every connection, whether a legitimate request or a Slowloris attempt, must now traverse the active authorization filter chain before the timeout mechanism closes it. The policy adds evaluation overhead without contributing additional security value in this specific context, since the proxy's inherent resilience already handles the threat. Linkerd's CPU decreased from approximately 306m to 260m under active policy, consistent with the Efficiency of Rejection pattern, suggesting that its lighter filter chain adds less evaluation overhead per connection than Istio's in this scenario.\n"
            elif sid == "Avail-Storm":
                typ_code += "As with EX-3, both meshes blocked the volumetric storm in their No-Policy states, and the baseline Kubernetes environment remained vulnerable. This again confirms that the protection is architectural: the sidecar proxy's connection management and timeout enforcement provide default resilience against flood-based availability attacks independent of any configured L7 policy. The finding should be understood as a baseline security dividend of service mesh adoption rather than an outcome of deliberate policy design. The CPU behaviour under active policy enforcement here diverges from the pattern observed in EX-3 in a way that illuminates the difference between the two attack types. In EX-3, Istio's CPU increased under With-Policy enforcement because each Slowloris connection, though ultimately timed out, still required ongoing tracking and filter chain traversal while it remained open. In Avail-Storm, both meshes show CPU decreasing under active policy, Istio from approximately 383m to 303m and Linkerd from 301m to 213m. A volumetric storm generates discrete high-rate requests rather than persistent connections, allowing the proxy to shed each request quickly at the edge once the policy's connection-level rules are engaged. Fast rejection of short-lived requests is computationally cheap, producing the Efficiency of Rejection effect that Slowloris, by its nature, prevents. Linkerd's p95 latency increased from approximately 110ms to 157ms under active policy despite the attack being blocked in both states. This reflects the *Instrumentation Tax*: with the threat already neutralised by inherent proxy behaviour, the policy adds filter chain evaluation overhead without contributing additional security value, producing a latency cost without a corresponding security gain. The same dynamic was observed in Istio's EX-3 CPU spike, though here it manifests as latency rather than compute overhead, consistent with the architectural difference between the two proxies' enforcement paths.\n"
            elif sid == "JWT-1":
                typ_code += "Both meshes blocked access to the restricted resource in the absence of a valid cryptographic token, but the enforcement mechanisms are architecturally distinct and the distinction carries meaningful security implications. Istio performed native `RS256` signature validation at the proxy layer, evaluating the token's cryptographic integrity before any request was permitted to proceed. Linkerd's enforcement, by contrast, operated through path exclusion: access to the restricted route was denied based on the absence of a recognized authorization attribute rather than through independent verification of the token's validity. In practical terms, this gap means the two approaches offer different levels of resilience against token-based attacks beyond simple absence. Istio would reject a request carrying a forged, expired, or structurally malformed token because the signature check would fail regardless of what the token claims. Linkerd's path exclusion approach, depending on policy configuration, may not provide the same guarantee if an attacker presents a syntactically plausible but cryptographically invalid token that satisfies a surface-level policy match. For environments where JWT tokens are the primary identity primitive across services, this represents a meaningful depth-of-defense gap that architects should account for when selecting a mesh. On the performance side, both meshes exhibited a reduction in CPU consumption under active policy enforcement, Istio from approximately 360m to 327m, and Linkerd from 301m to 247m. The pattern is consistent with the Efficiency of Rejection: early termination of unauthorized requests at the proxy layer avoids the cost of upstream processing regardless of whether the termination is cryptographic or route-based. Linkerd's proportionally larger CPU reduction under a shallower enforcement mechanism suggests that the overhead savings from fast rejection outweigh the cost of the validation depth itself at this traffic volume.\n"
            elif sid == "Exfil-Chain":
                typ_code += "Both meshes successfully blocked the chained attack under active L7 policy, but the mechanism by which each achieves this outcome differs in a way that has direct implications for how their respective security coverage should be understood. Istio intercepts the chain through its egress filtering capability, the same mechanism demonstrated in EX-1. The internal data read and the subsequent exfiltration attempt are both subject to policy evaluation, and either stage can be terminated independently. This represents comprehensive coverage of the attack surface: even if the internal read were permitted, the egress step would still be blocked. Linkerd's success here requires a more precise interpretation. As established in EX-1, Linkerd cannot enforce policy against outbound traffic to external domains. Its block in this scenario is achieved by severing the first stage of the chain: the `HTTPRoute` policy prevents the internal data read from completing, which means the exfiltration step is never reached. The chain is broken at the intra-cluster access control layer rather than at the egress boundary. This is a meaningful distinction because it means Linkerd's coverage of this attack pattern is conditional on the chain having an internal HTTP step that its policy model can intercept. A variant of the attack that accessed already-accessible data before exfiltrating it would not be stopped by the same policy, since the egress step would remain outside Linkerd's enforcement boundary. Both meshes returned clean HTTP `403` responses across all three runs, and CPU consumption decreased under active enforcement in both cases, consistent with the Efficiency of Rejection pattern observed throughout the egress scenarios.\n"
            elif sid == "Combined-HTTP":
                typ_code += "Istio successfully blocked the simultaneous multi-vector evasion attempt across all three runs while Linkerd remained vulnerable. The distinction goes deeper than a difference in raw parsing capability between Envoy and Linkerd's Rust-based proxy. The more precise explanation lies in how each mesh evaluates policy against composite requests. Linkerd's authorization model evaluates `HTTPRoute` rules on a per-route basis. Each individual policy rule is assessed against the traffic stream independently, which works effectively when an attack presents a single vector that a single rule can match and reject. A multi-vector evasion attack deliberately constructs a request that simultaneously combines path manipulation, header injection, and other evasion techniques in a way that no single rule is designed to catch in isolation. The individual components of the request may each appear to satisfy different policy rules independently, while the combined intent and effect of the simultaneous vectors constitutes the attack. Linkerd's per-route evaluation model has no mechanism for holistic request assessment that evaluates the interaction between simultaneous vectors. Istio's Envoy-based proxy applies a composite filter chain that evaluates the full request context before making an authorization decision. The simultaneous presence of multiple evasion indicators is visible to the filter chain as a whole, allowing Envoy to catch combinations that would evade any single rule evaluated in isolation. Linkerd's CPU decreased from approximately 318m to 247m under active policy despite the attack succeeding, a pattern now observed consistently across scenarios where Linkerd's policy is applied but the relevant enforcement layer is not reached. By this point in the dataset, this CPU signature serves as a reliable indicator that a policy primitive mismatch exists between the attack vector and the enforcement capability deployed.\n"
            elif sid == "DG-1":
                typ_code += "Istio successfully blocked HTTP traffic directed at a port explicitly configured and named for gRPC, while Linkerd remained vulnerable across all three runs despite an active policy. The divergence reflects a fundamental difference in how each mesh handles the relationship between port declarations and protocol enforcement. Istio's Envoy-based proxy applies strict port-protocol binding. When a port is declared as gRPC, Envoy expects the traffic arriving on that port to conform to the gRPC framing specification. HTTP traffic that does not satisfy this expectation is rejected at the protocol validation stage before any application-layer policy evaluation is necessary. Linkerd's transparent proxy model operates differently: it performs protocol detection on incoming traffic and routes it based on what the traffic actually is rather than what the port declaration specifies. This flexibility is by design and serves legitimate operational purposes, but its consequence in a security context is that an attacker who knows the mesh architecture can deliberately send non-conforming traffic to a named port as a mechanism to evade route-level policies that were written assuming a specific protocol. The CPU data adds a further observation. Linkerd recorded a modest decrease in CPU consumption under active policy enforcement despite the attack succeeding, from approximately 288m to 259m. This indicates that the policy was applied and influenced some aspect of proxy processing without producing a security outcome. The compute cost of policy evaluation was incurred without the corresponding security benefit, which is a relevant consideration for operators assessing the overhead of policy deployment in environments where Linkerd's protocol flexibility creates enforcement gaps of this kind.\n"
            elif sid == "Full-Comp":
                typ_code += "Both meshes were ultimately vulnerable under the full compromise scenario, but the manner in which each failed is architecturally distinct and operationally significant. Istio's failure mode is one of degradation under complexity. The Envoy filter chain continued to attempt evaluation of the multi-vector payload, producing latency in the range of 164ms to 187ms across runs as the proxy processed the composite attack. The system slowed under the burden of inspecting traffic it could not fully classify and reject, but it did not abandon inspection entirely. This represents a fail-slow pattern: security enforcement degraded under extreme stress without collapsing, which preserves partial observability and leaves the filter chain in a state where recovery through policy adjustment or connection flushing remains possible. Linkerd's failure mode is categorically different. Across all three runs, the With-Policy state produced p95 latency between 5.78ms and 6.26ms and throughput between 13,035 and 14,296 RPS. These figures are not a performance achievement. They indicate that under the complexity of the full compromise payload, Linkerd's proxy abandoned L7 inspection entirely and began forwarding traffic at near line speed without policy evaluation. This is a fail-open pattern under extreme stress: rather than slowing to process what it cannot classify, the proxy passed the traffic through uninspected. The consistency of this behaviour across all three runs confirms it is a reproducible proxy degradation mode rather than a transient anomaly. The practical implication of this distinction is significant for operators. A fail-slow mesh under catastrophic failure preserves some security posture and produces observable signals, elevated latency and degraded throughput, that monitoring systems can detect and alert on. A fail-open mesh under the same conditions passes malicious traffic at high speed while appearing to function normally from a throughput perspective, producing no signal that an attack is in progress. In high-compliance environments where the failure mode of the security layer is itself a risk consideration, the qualitative difference between how Istio and Linkerd behave at their respective breaking points is as relevant as their performance under normal operating conditions.\n"
            else:
                typ_code += "The results for " + sid + " confirm that while the baseline and permissive mesh states are vulnerable, the application of L7 policies effectively mitigates the threat with measurable performance overhead.\n"

    typ_code += """
== Key Architectural Discovery: Ghost Connections
A critical operational discovery emerged during the transition between experimental states in this study. Both Istio and Linkerd exhibited *Ghost Connection* behaviour, where existing persistent TCP connections established via `HTTP Keep-Alive` during a permissive No-Policy run continued to be honoured after a restrictive With-Policy was applied. Requests transmitted over these pre-existing connections bypassed the newly enforced policy entirely until the connections were explicitly terminated through an active rollout restart.

The empirical evidence for this behaviour is present in the dataset. In Run 2, the Linkerd-No-Policy state for HTTP-1 recorded a `Status 0` result despite no policy being active at that point. This is a manifestation of connection lifecycle friction during state transitions: as the orchestrator moved between experimental phases, a stale Keep-Alive connection from a prior state caused the proxy to reset the stream when its metadata no longer matched the expected session context. Rather than a false positive or a data error, this result is a direct observation of the mesh proxy encountering an inconsistency between connection state and the policy it was in the process of loading.

The underlying cause is that L7 policy enforcement in both meshes operates at the point of connection establishment rather than on every individual request within an existing connection. Once a TCP connection is open and has been authorised under a permissive policy, subsequent requests on that connection inherit the authorisation decision made at connection time. A new restrictive policy applied after the connection was established does not retroactively invalidate the session. The connection must be closed and re-established for the new policy to be evaluated at the handshake stage.

The propagation mechanism of each mesh introduces additional nuance. Istio uses a push-based `xDS` distribution model where the control plane actively pushes policy updates to all sidecar proxies simultaneously. While this ensures broad propagation, it does not guarantee that all existing connections are immediately re-evaluated against the new policy. Linkerd uses a pull-based just-in-time model where proxies request destination information on first contact. This reduces control plane load but means policy synchronisation timing is dependent on individual proxy request cycles rather than a centralised push event. In both cases, the security posture during the propagation window is the posture of the previous state, not the intended new state.

The security implication of this window is concrete. An attacker maintaining an active persistent connection at the moment a remediation policy is deployed retains the access level of the pre-remediation state for the lifetime of that connection. In a post-exploitation lateral movement scenario, this means that deploying a policy in response to a detected intrusion does not immediately contain an active attacker who already has open connections to internal services. Policy deployment must be coupled with active connection flushing, through mechanisms such as the automated rollout restarts implemented in this study's orchestrator, to ensure the security posture is fully synchronised with the intended state. Zero Trust policy management must therefore be understood as an operational lifecycle activity rather than a static configuration event.

== Summary of Comparative Resource Trends

""" + memory_grouped_bar_chart() + """
*The Lightweight Paradox*
The experimental data reveals a reversal of expected resource trends. Linkerd is marketed as a lightweight, resource-efficient mesh, yet its memory consumption in the hardened state averaged 129.38 MiB compared to Istio's 119.14 MiB. The more operationally significant finding is not the mean figure but the variance. Linkerd's memory usage escalated from a minimum of 23 MiB at the start of a run to a maximum of 221 MiB under sustained connection load across the experimental cycles. Istio's footprint, while higher at baseline, remained stable and predictable across the same conditions. This distinction matters in production capacity planning: a system with a high but stable memory ceiling is easier to provision and monitor than one whose memory consumption is highly sensitive to connection history and telemetry accumulation. The state-dependency of Linkerd's memory profile is consistent with its pull-based just-in-time service discovery model, where proxy state grows as the mesh accumulates connection metadata over the lifetime of a run, a behaviour that also contributes to the Ghost Connection dynamics discussed in Section 5.2.

*The Efficiency of Rejection*
A counter-intuitive trend observed across multiple scenarios is that CPU consumption decreases when security policies are enforced compared to permissive states. This was most dramatically demonstrated in EX-2, where Istio's active rate limiter collapsed p95 latency from approximately 188ms to 9.59ms while throughput increased from roughly 688 RPS to over 9,000 RPS. The same effect appeared in Avail-Storm, where both meshes showed CPU reductions under active policy despite blocking the attack in both states. Critically, this pattern was also observed in application layer scenarios with no volumetric load component, including HTTP-2, HTTP-3, and IP-1, where policy enforcement produced CPU reductions in both meshes even at normal traffic volumes. The mechanism is consistent across all cases: when a policy is active, the sidecar terminates unauthorised requests at the earliest applicable check in the filter chain, avoiding the higher-cost operations of upstream connection establishment, response proxying, and data streaming. Early rejection is computationally cheaper than completing the request lifecycle for traffic that would ultimately be blocked, and this saving is observable at any traffic volume where the rejected requests would otherwise require meaningful upstream processing.

#figure(
  caption: [The Efficiency of Rejection: with active policy the proxy terminates unauthorised requests at the earliest applicable authorization check, skipping upstream connection establishment, response proxying, and data streaming. Most dramatically demonstrated in EX-2 — Istio p95 latency collapsed from 188ms to 9.59ms and throughput rose from 688 to 9,025 RPS under active rate limiting.],
  kind: image,
)[
  #block(width: 100%, stroke: 0.5pt + luma(200), inset: 14pt, radius: 4pt, breakable: false)[
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 20pt,
      align: top,
      [
        #align(center)[*Without Active Policy*]
        #v(8pt)
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[Inbound Request]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[mTLS Handshake]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[L7 Parse + Route Match]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[Upstream Connection Established]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[Response Proxied + Streamed]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: rgb("#fadbd8"), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[`200` — attack succeeds]]
        ]
        #v(6pt)
        #align(center)[#text(size: 8pt, fill: luma(80))[Full proxy lifecycle incurred on every request]]
      ],
      [
        #align(center)[*With Active Policy*]
        #v(8pt)
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[Inbound Request]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(238), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[mTLS Handshake]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: rgb("#d5f5e3"), stroke: 0.6pt + rgb("#1e8449"))[
          #align(center)[#text(size: 9pt)[Authorization Check: *DENY*]]
        ]
        #align(center)[#text(size: 11pt)[↓]]
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: rgb("#d6eaf8"), stroke: 0.4pt + luma(180))[
          #align(center)[#text(size: 9pt)[`403` / `429` — returned immediately]]
        ]
        #v(4pt)
        #rect(width: 100%, radius: 2pt, inset: (x: 8pt, y: 6pt), fill: luma(245), stroke: 0.4pt + luma(200))[
          #align(center)[#text(size: 8pt, style: "italic")[Upstream connection, response proxying, and data streaming: *skipped*]]
        ]
        #v(6pt)
        #align(center)[#text(size: 8pt, fill: luma(80))[EX-2: 188ms → 9.59ms p95 · 688 → 9,025 RPS]]
      ]
    )
  ]
]

*The Instrumentation Tax*
The Efficiency of Rejection is not universal. In scenarios where the attack volume is insufficient to generate meaningful rejection savings, or where the proxy's inherent behaviour already neutralises the threat before policy evaluation occurs, enforcing an active policy produces a net increase in overhead. This was observed in HTTP-1 and HTTP-3, where Linkerd's latency increased under active policy without a corresponding throughput change, reflecting the fixed cost of traversing the newly activated authorization filter chain on every legitimate request. The most pronounced manifestation was in EX-3, where Istio's CPU increased from approximately 355m to 614m under With-Policy enforcement despite the attack being blocked in both states. With the Slowloris threat already neutralised by the proxy's built-in timeout management, the active filter chain added evaluation overhead to every connection without contributing additional security value. The Instrumentation Tax and the Efficiency of Rejection are therefore competing forces whose net outcome depends on the relationship between the attack volume, the cost of the rejected requests, and whether the proxy's inherent capabilities already address the threat independently of the configured policy.

*The Policy Overhead Without Security Outcome Pattern*
A fourth resource pattern emerged consistently across scenarios where Linkerd's enforcement boundary did not match the attack vector: CPU consumption decreased under active policy enforcement despite the attack succeeding. This was observed in DG-1, DG-2, EX-2, EX-1, and Combined-HTTP. In each case, the policy was applied, influenced proxy processing to a degree measurable in CPU consumption, but did not engage the enforcement layer relevant to the specific attack. By the latter scenarios in the dataset, this CPU signature, a modest decrease in Linkerd's compute consumption under a policy that produces no security outcome, had become a reliable indicator of a mismatch between the policy primitive deployed and the attack vector being tested. It also has a practical implication for operators: a reduction in resource consumption under active policy is not in itself evidence that the policy is working as intended. In Linkerd environments particularly, resource metrics must be interpreted alongside security outcome data rather than in isolation.
"""

    with open("paper/results_discussion.typ", "w") as f:
        f.write(typ_code)

if __name__ == "__main__":
    generate()
