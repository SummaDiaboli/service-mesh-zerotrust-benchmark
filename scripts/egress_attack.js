const http = require('http');
const start = Date.now();

// EX-1: Egress Exfiltration
// Simulating an attacker trying to send stolen data to an external command-and-control server.
const options = {
    hostname: 'google.com', // Using google.com as a "safe" proxy for an external attacker domain
    port: 80,
    path: '/',
    method: 'GET',
    timeout: 5000
};

const req = http.request(options, (res) => {
    const duration = Date.now() - start;
    // If we get a response from the external world, the exfiltration is "successful" (Vulnerable)
    process.stdout.write(`${res.statusCode} ${duration.toFixed(2)}
`);
    process.exit(0);
});

req.on('error', (e) => {
    const duration = Date.now() - start;
    // 000 or any non-2xx/3xx usually indicates the mesh blocked the egress
    process.stdout.write(`000 ${duration.toFixed(2)}
`);
    process.exit(0);
});

req.end();
