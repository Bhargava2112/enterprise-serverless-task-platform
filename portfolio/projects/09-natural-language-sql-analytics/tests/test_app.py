import unittest
from app import AnalyticsEngine,SemanticPlanner,UnsupportedQuery,demo_database
class SQLTests(unittest.TestCase):
 def setUp(self):self.engine=AnalyticsEngine(demo_database())
 def test_aggregation(self):
  result=self.engine.execute('revenue by region')
  self.assertEqual(result['rows'][0]['revenue_cents'],2250)
 def test_filter_and_params(self):
  result=self.engine.execute('orders in region west from 2026-01-01 to 2026-01-31')
  self.assertEqual(result['rows'][0]['order_count'],1)
  self.assertEqual(result['parameters'][0],'west')
 def test_injection_not_interpolated(self):
  with self.assertRaises(UnsupportedQuery):self.engine.execute('drop table orders')
  self.assertEqual(self.engine.execute('orders in region west')['rows'][0]['order_count'],2)
 def test_reject_unknown(self):
  with self.assertRaises(UnsupportedQuery):self.engine.execute('show private customer addresses')
 def test_limits(self):
  with self.assertRaises(UnsupportedQuery):SemanticPlanner().compile('revenue',limit=9999)
if __name__=='__main__':unittest.main()
