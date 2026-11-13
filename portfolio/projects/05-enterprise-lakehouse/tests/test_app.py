import unittest
from app import Lakehouse,QualityError
VALID={'event_id':'e1','customer_id':'c1','amount_cents':199,'occurred_at':'2026-01-01T00:00:00Z'}
class LakeTests(unittest.TestCase):
 def setUp(self):self.l=Lakehouse()
 def test_incremental_replay(self):
  self.assertEqual(self.l.ingest([VALID],'run1')['accepted'],1)
  self.assertTrue(self.l.ingest([VALID],'run1')['replay'])
  self.assertEqual(self.l.quality_metrics()['silver'],1)
  with self.assertRaises(QualityError):self.l.ingest([{**VALID,'amount_cents':5}],'run1')
 def test_quarantine(self):
  res=self.l.ingest([VALID,{'event_id':'bad','customer_id':'','amount_cents':-5,'occurred_at':'BAD'}],'r')
  self.assertEqual((res['accepted'],res['rejected']),(1,1));self.assertEqual(self.l.gold_revenue_by_customer(),[('c1',1,199)])
 def test_invalid_key_rejects_transaction(self):
  with self.assertRaises(QualityError):self.l.ingest([VALID,{'x':1}],'r')
  self.assertEqual(self.l.quality_metrics()['bronze'],0)
 def test_scd2(self):
  self.assertTrue(self.l.upsert_customer('c1','bronze',1))
  self.assertFalse(self.l.upsert_customer('c1','bronze',2))
  self.assertTrue(self.l.upsert_customer('c1','gold',3))
  self.assertEqual(self.l.db.execute('SELECT segment,valid_from,valid_to FROM dim_customer ORDER BY valid_from').fetchall(),[('bronze',1,3),('gold',3,None)])
  with self.assertRaises(ValueError):self.l.upsert_customer('c1','silver',2)
if __name__=='__main__':unittest.main()
