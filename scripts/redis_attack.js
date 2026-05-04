const net = require('net');
const start = Date.now();
const scenario = process.argv[2] || 'DB-1';
const namespace = process.argv[3] || 'ns-baseline';

const host = `redis.${namespace}.svc.cluster.local`;
const port = 6379;

const command = scenario === 'DB-1' ? '*1\r\n$8\r\nFLUSHALL\r\n' : '*2\r\n$4\r\nKEYS\r\n$1\r\n*\r\n';

const client = net.createConnection({ port: port, host: host }, () => {
    client.write(command);
});

client.setTimeout(3000);

client.on('data', (data) => {
    const duration = Date.now() - start;
    const resp = data.toString();
    let status = resp.includes('+OK') || resp.startsWith('*') ? '200' : '403';
    process.stdout.write(`${status} ${duration.toFixed(2)}\n`);
    client.destroy();
    process.exit(0);
});

function fail(msg) {
    const duration = Date.now() - start;
    process.stdout.write(`403 ${duration.toFixed(2)}\n`);
    client.destroy();
    process.exit(0);
}

client.on('error', (err) => { fail('error'); });
client.on('timeout', () => { fail('timeout'); });
setTimeout(() => { fail('hard-timeout'); }, 5000);
