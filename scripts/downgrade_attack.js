const net = require('net');
const start = Date.now();
const scenario = process.argv[2] || 'DG-1';
const namespace = process.argv[3] || 'ns-baseline';

const host = `payment-service.${namespace}.svc.cluster.local`;
const port = 50051;

const client = new net.Socket();
client.setTimeout(5000);

client.connect(port, host, () => {
    // Constructing the request as a single array of lines to avoid multi-line syntax issues
    const lines = [
        "GET /admin/keys HTTP/1.1",
        "Host: " + host,
        "X-User-Role: Admin",
        "Connection: close",
        "",
        ""
    ];
    client.write(lines.join("\r\n"));
});

client.on('data', (data) => {
    const duration = Date.now() - start;
    const response = data.toString();
    const match = response.match(/HTTP\/1\.\d\s+(\d{3})/);
    const status = match ? match[1] : '000';
    process.stdout.write(status + ' ' + duration.toFixed(2) + '\n');
    client.destroy();
    process.exit(0);
});

client.on('error', (e) => {
    const duration = Date.now() - start;
    process.stdout.write('000 ' + duration.toFixed(2) + '\n');
    process.exit(0);
});

client.on('timeout', () => {
    const duration = Date.now() - start;
    process.stdout.write('000 ' + duration.toFixed(2) + '\n');
    process.exit(0);
});
