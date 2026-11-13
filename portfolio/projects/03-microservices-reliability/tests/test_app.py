import unittest
from app import CircuitBreaker,Bulkhead,BulkheadFull,CircuitOpen,RetryPolicy,SLIMetrics,resilient_call
class ReliabilityTests(unittest.TestCase):
 def test_circuit_trip_and_recovery(self):
  now=[0];cb=CircuitBreaker(2,10,lambda:now[0])
  def fail():raise TimeoutError()
  for _ in range(2):
   with self.assertRaises(TimeoutError):cb.call(fail)
  self.assertEqual(cb.state,'open')
  with self.assertRaises(CircuitOpen):cb.call(lambda:'ok')
  now[0]=11;self.assertEqual(cb.call(lambda:'ok'),'ok');self.assertEqual(cb.state,'closed')
 def test_bulkhead_fails_fast(self):
  b=Bulkhead(1)
  with self.assertRaises(BulkheadFull):b.call(lambda:b.call(lambda:2))
  self.assertEqual(b.call(lambda:3),3)
 def test_retry_explicit_transients(self):
  calls=[0];delays=[]
  def flaky():
   calls[0]+=1
   if calls[0]<3:raise TimeoutError()
   return 'ok'
  self.assertEqual(RetryPolicy().run(flaky,sleeper=delays.append,jitter=lambda:0),'ok')
  self.assertEqual(calls[0],3);self.assertEqual(len(delays),2)
 def test_non_idempotent_operation_not_retried(self):
  calls=[0]
  def fail():calls[0]+=1;raise TimeoutError()
  with self.assertRaises(TimeoutError):resilient_call(fail,CircuitBreaker(),Bulkhead(1),RetryPolicy(),idempotent=False)
  self.assertEqual(calls[0],1)
 def test_metrics(self):
  m=SLIMetrics();self.assertIsNone(m.snapshot()['availability'])
  for i in range(100):m.record(i,success=i!=99)
  self.assertAlmostEqual(m.snapshot()['availability'],.99)
  self.assertEqual(m.snapshot()['p95_ms'],94)
if __name__=='__main__':unittest.main()
