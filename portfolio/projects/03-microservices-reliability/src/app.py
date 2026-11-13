"""Resilience primitives for services: circuit breakers, bulkheads, budgets, SLOs."""
from dataclasses import dataclass
from collections import deque
from threading import BoundedSemaphore,Lock
from time import monotonic,sleep
import random

class CircuitOpen(RuntimeError):pass
class BulkheadFull(RuntimeError):pass
class RetryExhausted(RuntimeError):pass

@dataclass(frozen=True)
class RetryPolicy:
    attempts: int=3
    base_delay: float=.02
    cap_delay: float=.2
    def __post_init__(self):
        if not 1<=self.attempts<=20 or self.base_delay<0 or self.cap_delay<self.base_delay:
            raise ValueError('unsafe retry configuration')
    def run(self,fn,*,transient=(TimeoutError,ConnectionError),sleeper=sleep,jitter=lambda:random.random()):
        """Retries only explicitly classified transient errors; no mutation automatically retried."""
        for attempt in range(self.attempts):
            try:return fn()
            except transient:
                if attempt==self.attempts-1:raise
                sleeper(min(self.cap_delay,self.base_delay*2**attempt)*(0.5+0.5*jitter()))

class CircuitBreaker:
    def __init__(self,threshold=5,recovery_seconds=30,clock=monotonic):
        if threshold<1 or recovery_seconds<=0:raise ValueError('invalid circuit settings')
        self.threshold=threshold;self.recovery=recovery_seconds;self.clock=clock
        self.failures=0;self.opened_at=None;self.trial=False;self._lock=Lock()
    def call(self,fn):
        with self._lock:
            if self.opened_at is not None:
                if self.clock()-self.opened_at<self.recovery or self.trial:raise CircuitOpen('open')
                self.trial=True
        try:
            result=fn()
        except Exception:
            with self._lock:
                self.failures+=1
                self.trial=False
                if self.failures>=self.threshold:self.opened_at=self.clock()
            raise
        else:
            with self._lock:self.failures=0;self.opened_at=None;self.trial=False
            return result
    @property
    def state(self):
        with self._lock:
            if self.opened_at is None:return 'closed'
            return 'half-open' if self.clock()-self.opened_at>=self.recovery else 'open'

class Bulkhead:
    def __init__(self,concurrency):
        if concurrency<1:raise ValueError('invalid concurrency')
        self.pool=BoundedSemaphore(concurrency)
    def call(self,fn):
        if not self.pool.acquire(blocking=False):raise BulkheadFull('queue at capacity')
        try:return fn()
        finally:self.pool.release()

class SLIMetrics:
    def __init__(self,max_samples=10000):
        self.samples=deque(maxlen=max_samples);self._lock=Lock()
    def record(self,elapsed_ms,success=True):
        if elapsed_ms<0:raise ValueError('negative latency')
        with self._lock:self.samples.append((elapsed_ms,success))
    def snapshot(self,availability_target=.999,latency_target_ms=200):
        with self._lock:values=list(self.samples)
        if not values:return {'total':0,'availability':None,'p95_ms':None,'error_budget_remaining':None}
        lat=sorted(x for x,_ in values);total=len(values);fail=sum(not ok for _,ok in values)
        percentile=lambda p:lat[max(0,int((total*p+99)//100)-1)]
        budget=max(0,(1-availability_target)*total-fail)
        return {'total':total,'availability':(total-fail)/total,
                'p95_ms':percentile(95),'latency_slo_met':percentile(95)<=latency_target_ms,
                'error_budget_remaining':round(budget,3)}

def resilient_call(fn,breaker,bulkhead,retry_policy=None,*,idempotent=False):
    """No hidden retries on non-idempotent operations."""
    run=lambda:breaker.call(lambda:bulkhead.call(fn))
    return retry_policy.run(run) if retry_policy and idempotent else run()

if __name__=='__main__':
    metrics=SLIMetrics();metrics.record(42);print(metrics.snapshot())
