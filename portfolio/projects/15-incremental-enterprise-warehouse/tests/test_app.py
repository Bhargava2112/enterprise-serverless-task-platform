import unittest
from app import Warehouse,WarehouseError
class WarehouseTests(unittest.TestCase):
 def setUp(self):self.w=Warehouse()
 def test_scd_historical_attribution(self):
  prod=[('p1','gadgets','2026-01-01'),('p1','electronics','2026-03-01')]
  ev=[{'event_id':'e1','product_id':'p1','amount_cents':100,'sale_date':'2026-02-01'},
      {'event_id':'e2','product_id':'p1','amount_cents':500,'sale_date':'2026-04-01'}]
  self.assertEqual(self.w.load_sales('b1',ev,prod)['accepted'],2)
  self.assertEqual(self.w.category_revenue(),[('electronics',1,500),('gadgets',1,100)])
 def test_idempotent_batch(self):
  prod=[('p1','gadgets','2026-01-01')]
  self.w.load_sales('b1',[],prod)
  self.assertTrue(self.w.load_sales('b1',[],prod)['replay'])
  with self.assertRaises(WarehouseError):self.w.load_sales('b1',[],[])
 def test_unmapped_quarantine(self):
  ev=[{'event_id':'e1','product_id':'missing','amount_cents':300,'sale_date':'2026-01-01'}]
  result=self.w.load_sales('b1',ev,[])
  self.assertEqual(result['quarantined'],1);self.assertEqual(self.w.reconcile()['facts'],0)
 def test_atomic_rollback(self):
  with self.assertRaises(WarehouseError):self.w.load_sales('b1',[{'not_an_id':1}],[('p1','g','2026-01-01')])
  self.assertEqual(self.w.db.execute('SELECT COUNT(*) FROM dim_product').fetchone()[0],0)
if __name__=='__main__':unittest.main()
