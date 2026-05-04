const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'HTTP-1';
const namespace = process.argv[3] || 'ns-baseline';

const options = {
    hostname: `backend-api.${namespace}.svc.cluster.local`,
    port: 80,
    path: '/api/internal/secrets',
    method: 'GET',
    timeout: 5000
};

const req = http.request(options, (res) => {
    const duration = Date.now() - start;
    process.stdout.write(res.statusCode + ' ' + duration.toFixed(2) + '\n');
    process.exit(0);
});

req.on('error', (e) => {
    const duration = Date.now() - start;
    process.stdout.write('000 ' + duration.toFixed(2) + '\n');
    process.exit(0);
});

req.end();
