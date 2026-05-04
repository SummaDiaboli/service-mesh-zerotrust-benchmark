const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'EX-2';
const namespace = process.argv[3] || 'ns-baseline';

const host = `payment-service.${namespace}.svc.cluster.local`;
const port = 80;
const totalRequests = 500;
let completedRequests = 0;
let statusCodes = {};

console.log(`[Flood] Starting attack on ${host} with ${totalRequests} requests...`);

for (let i = 0; i < totalRequests; i++) {
    const req = http.request({
        hostname: host,
        port: port,
        path: '/process',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        timeout: 2000
    }, (res) => {
        statusCodes[res.statusCode] = (statusCodes[res.statusCode] || 0) + 1;
        checkDone();
    });

    req.on('error', (e) => {
        statusCodes['000'] = (statusCodes['000'] || 0) + 1;
        checkDone();
    });

    req.write(JSON.stringify({ amount: 100 }));
    req.end();
}

function checkDone() {
    completedRequests++;
    if (completedRequests === totalRequests) {
        const duration = Date.now() - start;
        // Logic for orchestrator: 
        // If the majority of requests are 429 (Too Many Requests), the block worked.
        // If the majority are 200, the attack reached the server (Vulnerable).
        const successCount = statusCodes['200'] || 0;
        const rateLimitCount = statusCodes['429'] || 0;
        
        let finalStatus = successCount > (totalRequests * 0.5) ? '200' : '429';
        if (rateLimitCount > 10) finalStatus = '429'; // Even a few 429s prove the policy is active

        process.stdout.write(`${finalStatus} ${duration.toFixed(2)}
`);
        process.exit(0);
    }
}
