import unittest
from app import CDCSource,CDCSink,OutOfSequence,replicate_once
class CDCTests(unittest.TestCase):
 def setUp(self):self.s=CDCSource();self.t=CDCSink()
 def test_replication_and_replay(self):
  self.s.change('a','UPSERT',{'name':'alice','new_field':True})
  self.assertEqual(replicate_once(self.s,self.t),1)
  self.assertEqual(replicate_once(self.s,self.t),0)
  self.assertEqual(self.t.snapshot()['a']['new_field'],True)
  self.s.change('a','DELETE');self.assertEqual(replicate_once(self.s,self.t),1)
  self.assertEqual(self.t.snapshot(),{})
 def test_order_guarantees(self):
  self.s.change('a','UPSERT',{'v':1});self.s.change('a','UPSERT',{'v':2})
  events=self.s.poll()
  with self.assertRaises(OutOfSequence):self.t.apply_batch('orders',[events[1]])
  self.assertEqual(self.t.last_seq('orders'),0)
  self.assertEqual(self.t.snapshot(),{})
  self.t.apply_batch('orders',events);self.assertEqual(self.t.snapshot()['a']['v'],2)
 def test_idempotent_batch(self):
  self.s.change('a','UPSERT',{'v':1});events=self.s.poll()
  self.assertEqual(self.t.apply_batch('orders',events),1)
  self.assertEqual(self.t.apply_batch('orders',events),0)
 def test_validation(self):
  with self.assertRaises(ValueError):self.s.change('x','UPSERT',None)
  with self.assertRaises(ValueError):self.s.poll(limit=0)
if __name__=='__main__':unittest.main()
