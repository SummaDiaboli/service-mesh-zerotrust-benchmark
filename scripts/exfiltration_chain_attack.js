const http = require('http');
const start = Date.now();
const namespace = process.argv[3] || 'ns-baseline';

// Exfiltration Chain: HTTP-1 (Read) + EX-1 (Exfiltrate)
async function runChain() {
    console.error(`[Chain] Step 1: Attempting to read internal secrets from backend-api...`);
    
    const step1 = await new Promise((resolve) => {
        const req = http.request({
            hostname: `backend-api.${namespace}.svc.cluster.local`,
            port: 80,
            path: '/api/internal/secrets',
            method: 'GET',
            timeout: 3000
        }, (res) => {
            res.on('data', () => {});
            res.on('end', () => resolve(res.statusCode));
        });
        req.on('error', () => resolve('000'));
        req.on('timeout', () => { req.destroy(); resolve('000'); });
        req.end();
    });

    console.error(`[Chain] Step 1 Result: ${step1}`);

    console.error(`[Chain] Step 2: Attempting to exfiltrate data to google.com...`);
    const step2 = await new Promise((resolve) => {
        const req = http.request({
            hostname: 'google.com',
            port: 80,
            path: '/',
            method: 'GET',
            timeout: 3000
        }, (res) => {
            res.on('data', () => {});
            res.on('end', () => resolve(res.statusCode));
        });
        req.on('error', () => resolve('000'));
        req.on('timeout', () => { req.destroy(); resolve('000'); });
        req.end();
    });

    console.error(`[Chain] Step 2 Result: ${step2}`);

    // LOGIC: 
    // The chain is SUCCESSFUL (Vulnerable) only if BOTH steps worked (200/301/302).
    // If either step is blocked (403/404/000), the chain is BROKEN (Blocked).
    const s1Success = [200, 201].includes(step1);
    const s2Success = [200, 301, 302].includes(step2);

    const finalStatus = (s1Success && s2Success) ? '200' : '403';
    const duration = Date.now() - start;

    process.stdout.write(`${finalStatus} ${duration.toFixed(2)}
`);
    process.exit(0);
}

runChain();
