import express, { Request, Response, NextFunction } from 'express';
import Redis from 'ioredis'

const app = express();
const port = 3000;

// Service name 'redis' resolves via K8s DNS
const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379'
const redis = new Redis(redisUrl)

redis.on('connect', () => console.log(`Connected to Redis at ${redisUrl}`))
redis.on('error', (err) => console.error('Redis Connection error:', err))

interface CustomRequest extends Request {
  isAdmin?: boolean;
}

const adminCheck = (req: CustomRequest, res: Response, next: NextFunction) => {
  const role = req.headers['x-role'];
  if (role === 'admin') {
    req.isAdmin = true;
  } else {
    req.isAdmin = false;
  }
  next();
};

app.use(express.json());

app.get('/', (req: Request, res: Response) => {
  res.send({ status: 'Backend API is running', mode: 'VULNERABLE' });
});

app.delete('/api/users/:id', async (req: Request, res: Response) => {
  const userId = req.params.id;
  try {
    const result = await redis.del(`user:${userId}`);
    
    if (result === 1) {
      console.log(`User ${userId} deleted via insecure endpoint!`);
      res.status(200).send({ message: `User ${userId} deleted successfully`, deleted: true });
    } else {
      res.status(404).send({ message: `User ${userId} not found`, deleted: false });
    }
  } catch (err) {
    console.error(err);
    res.status(500).send({ error: 'Database error' });
  }
});

app.get('/api/internal/secrets', async (req: Request, res: Response) => {
  try {
    const secret = await redis.get('secret_flag');
    console.log(`Secret flag accessed!`);
    res.status(200).send({ 
      flag: secret || "FLAG_NOT_FOUND_CHECK_SEEDING",
      warning: "This is a restricted internal endpoint." 
    });
  } catch (err) {
    res.status(500).send({ error: 'Database error' });
  }
});

app.get('/api/admin/config', adminCheck, (req: CustomRequest, res: Response) => {
  if (req.isAdmin) {
    console.log(`Admin config accessed via spoofed header!`);
    res.send({
      status: "System Critical",
      config: "v1.0.0-alpha",
      admin_access: "GRANTED"
    });
  } else {
    res.status(403).send({ error: "Access Denied: Admin role required" });
  }
});

app.listen(port, () => {
  console.log(`Backend API listening on port ${port}`);
});
