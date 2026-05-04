const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'DG-2-Comparison';
const namespace = process.argv[3] || 'ns-baseline';

const host = `payment-service.${namespace}.svc.cluster.local`;
const port = 80;

const options = {
    hostname: host,
    port: port,
    path: '/admin/keys',
    method: 'GET',
    headers: { 'X-User-Role': 'Admin' },
    timeout: 5000
};

const req = http.request(options, (res) => {
    const duration = Date.now() - start;
    process.stdout.write(`${res.statusCode} ${duration.toFixed(2)}
`);
    process.exit(0);
});

req.on('error', (e) => {
    const duration = Date.now() - start;
    process.stdout.write(`000 ${duration.toFixed(2)}
`);
    process.exit(0);
});

req.end();
