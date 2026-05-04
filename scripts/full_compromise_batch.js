
const http = require('http');
const net = require('net');
const start = Date.now();
const ns = process.argv[process.argv.length - 1]; 
const results = { IP1: 0, H1: 0, H3: 0, DB1: 0 };
let done = 0;
const fin = () => {
    done++;
    if(done===4){
        const v = Object.values(results).filter(s => [200,201,301,302].includes(parseInt(s)));
        const duration = Date.now() - start;
        process.stdout.write((v.length>0?'200':'403') + ' ' + duration.toFixed(2) + '\n');
        process.exit(0);
    }
};
const req = (h,p,m,hd,k) => {
    const r = http.request({hostname:h + "." + ns + ".svc.cluster.local", port:80, path:p, method:m, headers:hd, timeout:1500},res=>{
        res.on("data",()=>{});
        res.on("end",()=>{results[k]=res.statusCode;fin();});
    });
    r.on('error',()=>{results[k]=0;fin();});
    r.on('timeout',()=>{r.destroy();results[k]=0;fin();});
    r.end();
};
req('audit-logger','/logs','DELETE',{'X-Forwarded-For':'127.0.0.1'},'IP1');
req('backend-api','/api/internal/secrets','GET',{},'H1');
req('payment-service','/admin/keys','GET',{'X-User-Role':'Admin'},'H3');
const c = net.createConnection({port:6379,host:"redis." + ns + ".svc.cluster.local"},()=>{c.write('*1\r\n$8\r\nFLUSHALL\r\n');});
c.setTimeout(1500);
c.on('data',d=>{results.DB1=d.toString().includes('+OK')?200:403;c.destroy();fin();});
c.on('error',()=>{results.DB1=0;fin();});
c.on('timeout',()=>{c.destroy();results.DB1=0;fin();});
