const http = require('http');
const start = Date.now();
const namespace = process.argv[3] || 'ns-baseline';

// Combined REST API Logic Attack (HTTP-1 to HTTP-4)
const attacks = [
    { id: 'HTTP-1', path: '/api/internal/secrets', method: 'GET', host: 'backend-api', headers: {} },
    { id: 'HTTP-2', path: '/logs', method: 'DELETE', host: 'audit-logger', headers: {} },
    { id: 'HTTP-3', path: '/admin/keys', method: 'GET', host: 'payment-service', headers: { 'X-User-Role': 'Admin' } },
    { id: 'HTTP-4', path: '/', method: 'GET', host: 'backend-api', headers: { 'Origin': 'http://evil.com' } }
];

let results = [];

async function runAttacks() {
    for (const atk of attacks) {
        const result = await new Promise((resolve) => {
            const options = {
                hostname: `${atk.host}.${namespace}.svc.cluster.local`,
                port: 80,
                path: atk.path,
                method: atk.method,
                headers: atk.headers,
                timeout: 3000
            };

            const req = http.request(options, (res) => {
                res.on('data', () => {});
                res.on('end', () => resolve({ id: atk.id, status: res.statusCode }));
            });

            req.on('error', () => resolve({ id: atk.id, status: '000' }));
            req.on('timeout', () => { req.destroy(); resolve({ id: atk.id, status: '000' }); });
            req.end();
        });
        results.push(result);
    }

    const vulnerabilities = results.filter(r => [200, 201, 301, 302].includes(r.status));
    const finalStatus = vulnerabilities.length > 0 ? '200' : '403';
    const duration = Date.now() - start;

    process.stdout.write(`${finalStatus} ${duration.toFixed(2)}\n`);
    console.error('Results:', JSON.stringify(results));
    process.exit(0);
}

runAttacks();
