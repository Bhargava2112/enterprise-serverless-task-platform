import tempfile,unittest
from pathlib import Path
from app import TestPlanner,ContractRunner,summarize_coverage,AnalysisError
SOURCE="""def clamp(n):\n if n < 0:\n  raise ValueError("negative")\n for i in range(n):\n  pass\n return n\n"""
class TestEngineeringTests(unittest.TestCase):
 def test_branch_planning(self):
  ideas=TestPlanner().analyze(SOURCE)
  kinds={x.kind for x in ideas}
  self.assertTrue({'branch','error-path','boundary','happy-path','invalid-input'}<=kinds)
 def test_invalid_python(self):
  with self.assertRaises(AnalysisError):TestPlanner().analyze('def x(:')
 def test_coverage_exposes_gaps(self):
  ideas=TestPlanner().analyze(SOURCE)
  result=summarize_coverage(ideas,{'happy-path','branch'})
  self.assertLess(result['coverage_ratio'],1)
 def test_trusted_test_runner(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test_sample.py').write_text('import unittest\nclass Check(unittest.TestCase):\n def test_a(self):self.assertTrue(True)\n')
   report=ContractRunner().run(p)
   self.assertEqual(report['status'],'passed',report['stderr'])
 def test_invalid_timeout(self):
  with self.assertRaises(ValueError):ContractRunner(0)
if __name__=='__main__':unittest.main()
