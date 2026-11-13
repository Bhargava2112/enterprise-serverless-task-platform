import unittest
from app import IncidentAnalyzer,DependencyGraph,Signal,anomaly_score
class RCATests(unittest.TestCase):
 def setUp(self):self.a=IncidentAnalyzer(DependencyGraph([('db','api'),('api','web')]))
 def test_root_dependency(self):
  signals=[Signal('x','db',95,'deployment',0,'db release'),Signal('y','other',99,'error',100,'unrelated')]
  report=self.a.analyze('web',100,signals)
  self.assertEqual(report['candidates'][0]['service'],'db')
  self.assertEqual(report['status'],'hypothesis')
 def test_no_evidence(self):
  self.assertEqual(self.a.analyze('web',100,[Signal('old','db',-1000,'error',1,'old')])['status'],'insufficient-evidence')
 def test_anomaly(self):
  self.assertGreater(anomaly_score([1,1,1,1],20),5)
 def test_ambiguity(self):
  x=[Signal('a','api',90,'error',1,'error'),Signal('b','api',90,'error',1,'error')]
  self.assertEqual(self.a.analyze('web',100,x)['status'],'needs-review')
 def test_graph(self):
  self.assertIsNone(DependencyGraph([]).impact_distance('a','b'))
if __name__=='__main__':unittest.main()
