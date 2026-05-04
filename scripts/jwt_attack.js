const http = require('http');
const start = Date.now();
const scenario = process.argv[2] || 'JWT-1';
const namespace = process.argv[3] || 'ns-baseline';
const tokenType = process.argv[4] || 'none'; // none, invalid, valid

const host = `payment-service.${namespace}.svc.cluster.local`;
const port = 80;

// Istio Sample JWT (Valid for the public Istio test JWKS)
const validToken = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRzdHlndzI3S3pOTnd6NHVreVpIVC1pZ3pLdlpYRE40SndLMnVsc09LNE0iLCJ0eXAiOiJKV1QifQ.eyJlbmQiOiI0Njg1OTg5NzAwIiwiaWF0IjoxNTEyMzg5NzAwLCJpc3MiOiJ0ZXN0aW5nQHNlY3VyZS5pc3Rpby5pbyIsInN1YiI6InRlc3RpbmdAc2VjdXJlLmlzdGlvLmlvIn0.Z969Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ69Z9iyZBD67_6UnZ-placeholder"; 

let headers = {
    'X-User-Role': 'Admin' // SPOOFED HEADER
};

if (tokenType === 'invalid') {
    headers['Authorization'] = "Bearer invalid-token-123";
} else if (tokenType === 'valid') {
    headers['Authorization'] = `Bearer ${validToken}`;
}

const options = {
    hostname: host,
    port: port,
    path: '/admin/keys',
    method: 'GET',
    headers: headers,
    timeout: 5000
};

const req = http.request(options, (res) => {
    const duration = Date.now() - start;
    process.stdout.write(`${res.statusCode} ${duration.toFixed(2)}\n`);
    process.exit(0);
});

req.on('error', (e) => {
    const duration = Date.now() - start;
    process.stdout.write(`000 ${duration.toFixed(2)}\n`);
    process.exit(0);
});

req.end();
