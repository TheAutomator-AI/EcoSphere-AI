"""Best-effort single-process write rate limiter; use Redis/WAF for production scale."""
from collections import defaultdict, deque
from time import monotonic
from fastapi import Request
from starlette.responses import JSONResponse

attempts:dict[str,deque]=defaultdict(deque)
async def write_rate_limit(request:Request, call_next):
    if request.method in ('POST','PUT','PATCH','DELETE') and request.url.path.startswith('/api/'):
        # Deliberately do not trust X-Forwarded-For from untrusted clients.
        ip=request.client.host if request.client else 'unknown'
        now=monotonic();bucket=attempts[ip]
        while bucket and now-bucket[0]>60:bucket.popleft()
        if len(bucket)>=60:return JSONResponse({'detail':'Too many write requests. Retry after one minute.'},status_code=429,headers={'Retry-After':'60'})
        bucket.append(now)
        if len(attempts)>10000:
            # Avoid long-lived unbounded memory under IP churn.
            attempts.clear()
    return await call_next(request)
