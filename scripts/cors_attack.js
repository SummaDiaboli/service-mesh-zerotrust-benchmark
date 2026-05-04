const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'HTTP-4';
const namespace = process.argv[3] || 'ns-baseline';

const options = {
    hostname: `backend-api.${namespace}.svc.cluster.local`,
    port: 80,
    path: '/',
    method: 'GET',
    headers: {
        'Origin': 'http://evil.com'
    },
    timeout: 5000
};

const req = http.request(options, (res) => {
    const duration = Date.now() - start;
    // In a CORS attack, if the response DOES NOT have the correct CORS headers
    // or if it allows the evil origin, it's a failure.
    // However, from a mesh perspective, we want the MESH to block the request 
    // or strip the headers.
    
    const allowOrigin = res.headers['access-control-allow-origin'];
    
    // If the mesh is defending, it might return 403 or simply not include the header.
    // If the server returns 200 AND there's no mesh policy, it's VULNERABLE.
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
