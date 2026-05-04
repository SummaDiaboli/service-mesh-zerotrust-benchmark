const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'IP-1';
const namespace = process.argv[3] || 'ns-baseline';

const options = {
    hostname: `audit-logger.${namespace}.svc.cluster.local`,
    port: 80,
    path: '/logs',
    method: 'DELETE',
    headers: {
        'X-Forwarded-For': '127.0.0.1',
        'X-Real-IP': '127.0.0.1'
    },
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
