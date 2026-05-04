import express, { Request, Response } from 'express';

const app = express();
const PORT = 8080;

app.use(express.json());

app.use((req, res, next) => {
  console.log(`[Payment-Service] ${req.method} ${req.path}`);
  next();
});

app.get('/admin/keys', (req: Request, res: Response) => {
  const userRole = req.headers['x-user-role'];

  if (userRole === 'Admin') {
    res.status(200).json({
      secret: "SUPER_SECRET_PAYMENT_KEYS_XYZ",
      status: "VULNERABLE: Header Auth Successful!",
      warning: "In a real Zero Trust mesh, this header should have been stripped or ignored."
    });
  } else {
    res.status(403).json({
      error: "Access Denied. Missing 'X-User-Role: Admin' header."
    });
  }
});

app.post('/payment.Service/Refund', (req: Request, res: Response) => {
  res.status(200).json({
    status: "REFUND PROCESSED",
    amount: 9999,
    warning: "VULNERABLE: Internal gRPC method exposed to public HTTP traffic!"
  });
});

app.post('/process', (req: Request, res: Response) => {
  const txId = Math.random().toString(36).substring(7);
  res.status(200).json({
    status: "Payment Processed",
    txId: `tx_${txId}`
  });
});

app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: "Healthy" });
});

app.listen(PORT, () => {
  console.log(`Payment Service (Express+TS) running on port ${PORT}`);
});
