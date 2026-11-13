import unittest
from app import Event,RetailStore,InsufficientStock,OutOfOrder
class RetailTests(unittest.TestCase):
 def setUp(self):self.db=RetailStore()
 def tearDown(self):self.db.close()
 def test_order_and_revenue(self):
  events=[Event.new('restock',1,'RESTOCK','A',10),Event.new('o1',1,'PURCHASE','A',2,150),Event.new('o1',2,'REFUND','A',1,150)]
  for e in events:self.assertTrue(self.db.apply(e))
  self.assertEqual(self.db.units('A'),9);self.assertEqual(self.db.revenue(),150)
  self.assertFalse(self.db.apply(events[1]))
 def test_insufficient_inventory_rolls_back(self):
  ev=Event.new('o1',1,'PURCHASE','A',1,400)
  with self.assertRaises(InsufficientStock):self.db.apply(ev)
  self.assertEqual(self.db.units('A'),0)
  self.assertTrue(self.db.apply(Event.new('o1',1,'RESTOCK','A',4)))
 def test_ordering(self):
  with self.assertRaises(OutOfOrder):self.db.apply(Event.new('x',2,'RESTOCK','A',1))
 def test_outbox_retry_deduplicates(self):
  ev=Event.new('x',1,'RESTOCK','A',5);self.db.enqueue(ev)
  def publisher(e):self.db.apply(e)
  self.assertEqual(self.db.dispatch_once(publisher),1)
  self.assertEqual(self.db.dispatch_once(publisher),0)
  self.assertFalse(self.db.apply(ev))
 def test_invalid(self):
  with self.assertRaises(ValueError):Event.new('x',0,'PURCHASE','A',2)
if __name__=='__main__':unittest.main()
