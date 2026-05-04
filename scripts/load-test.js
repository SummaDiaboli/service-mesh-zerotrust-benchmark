import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: __ENV.CONCURRENCY || 50,
  duration: __ENV.DURATION || '30s',
};

export default function () {
  const url = __ENV.TARGET_URL;
  if (url) {
    http.get(url);
  }
  // sleep(0.1); // Optional: add small sleep
}
