import express, { Request, Response } from 'express';

const app = express();
const PORT = 8080;

app.use(express.json());

// Logging Middleware
app.use((req, res, next) => {
  console.log(`[Audit-Logger] ${req.method} ${req.path}`);
  next();
});

app.delete('/logs', (req: Request, res: Response) => {
  console.warn("!!! ALERT: LOG WIPE INITIATED !!!");

  res.status(200).json({
    status: "ALL LOGS DELETED",
    warning: "VULNERABLE: Attack Successful! The mesh did not block this DELETE request.",
    timestamp: new Date().toISOString()
  });
});

app.post('/logs', (req: Request, res: Response) => {
  const logEntry = req.body;
  console.log("Log saved:", logEntry);

  res.status(201).json({
    status: "Log Entry Saved",
    id: Math.random().toString(36).substring(7)
  });
});

app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: "Healthy" });
});

app.listen(PORT, () => {
  console.log(`Audit Logger (Express+TS) running on port ${PORT}`);
});
