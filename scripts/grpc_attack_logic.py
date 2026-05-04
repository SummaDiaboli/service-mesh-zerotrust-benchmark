import json

def get_node_attack_payload(scenario, namespace, service_port=80):
    recipes = {
        "HTTP-2": {"svc": "audit-logger", "method": "DELETE", "path": "/logs", "headers": {}},
        "HTTP-3": {"svc": "payment-service", "method": "GET", "path": "/admin/keys", "headers": {"X-User-Role": "Admin"}},
        "RPC-1":  {"svc": "payment-service", "method": "POST", "path": "/payment.Service/Refund", 
                   "headers": {"Content-Type": "application/grpc+json"}, "body": '{"id":"atk"}'},
    }
    
    if scenario in ["DB-1", "DB-2"]:
        # Redis logic using net module - CLEAN SINGLE LINE OUTPUT
        command = '*1\\r\\n$8\\r\\nFLUSHALL\\r\\n' if scenario == 'DB-1' else '*2\\r\\n$4\\r\\nKEYS\\r\\n$1\\r\\n*\\r\\n'
        return f"""
const net = require('net');
const start = Date.now();
const client = net.createConnection({{ port: 6379, host: 'redis.{namespace}.svc.cluster.local' }}, () => {{
    client.write('{command}');
}});
client.setTimeout(3000);
client.on('data', (data) => {{
    const duration = Date.now() - start;
    let status = data.toString().includes('+OK') || data.toString().startsWith('*') ? '200' : '403';
    process.stdout.write(status + ' ' + duration.toFixed(2) + '\\n');
    client.destroy();
}});
client.on('error', () => {{ process.stdout.write('403 ' + (Date.now() - start).toFixed(2) + '\\n'); process.exit(0); }});
client.on('timeout', () => {{ process.stdout.write('403 ' + (Date.now() - start).toFixed(2) + '\\n'); process.exit(0); }});
"""

    if scenario not in recipes: return None
    r = recipes[scenario]
    target_host = f"{r['svc']}.{namespace}"
    headers_json = json.dumps(r.get("headers", {}))
    body_data = r.get("body", "")
    return f"""
const http = require('http');
const start = Date.now();
const options = {{ hostname: '{target_host}', port: {service_port}, path: '{r['path']}', method: '{r['method']}', headers: {headers_json}, timeout: 5000 }};
const req = http.request(options, (res) => {{
    const duration = Date.now() - start;
    let status = res.statusCode;
    if (res.headers['grpc-status'] && res.headers['grpc-status'] !== '0') status = 403;
    process.stdout.write(status + ' ' + duration.toFixed(2) + '\\n');
    process.exit(0);
}});
req.on('error', (e) => {{
    process.stdout.write('000 ' + (Date.now() - start).toFixed(2) + '\\n');
    process.exit(0);
}});
{f"req.write('{body_data}');" if body_data else ""}
req.end();
"""

def get_curl_attack_command(scenario, namespace, service_port=80):
    recipes = {
        "HTTP-2": {"svc": "audit-logger", "method": "DELETE", "path": "/logs", "headers": []},
        "HTTP-3": {"svc": "payment-service", "method": "GET", "path": "/admin/keys", "headers": ["X-User-Role: Admin"]},
        "RPC-1":  {"svc": "payment-service", "method": "POST", "path": "/payment.Service/Refund", 
                   "headers": ["Content-Type: application/grpc+json"], "body": '{"id":"atk"}'},
    }
    if scenario not in recipes: return None
    r = recipes[scenario]
    url = f"http://{r['svc']}.{namespace}:{service_port}{r['path']}"
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code} %{time_total}\\n", "-X", r['method'], "--connect-timeout", "5"]
    for h in r['headers']:
        cmd += ["-H", h]
    if r.get("body"):
        cmd += ["-d", r['body']]
    cmd.append(url)
    return cmd
