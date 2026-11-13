import unittest
from app import PolicyReviewer,gate,summarize
class CodeReviewTests(unittest.TestCase):
 def setUp(self):self.p=PolicyReviewer()
 def test_secrets_are_blocking(self):
  findings=self.p.review_file('x.py',"api_key = 'this_is_a_fake_test_credential'\n")
  self.assertFalse(gate(findings));self.assertEqual(findings[0].severity,'critical')
 def test_safe_code(self):
  self.assertTrue(gate(self.p.review_file('ok.py','def add(a,b):\n return a+b\n')))
 def test_ast_checks(self):
  findings=self.p.review_file('bad.py','try:\n 1 / 0\nexcept:\n pass\n')
  self.assertTrue(any(f.rule=='bare-except' for f in findings))
 def test_diff_line_numbers(self):
  diff='--- a/src/x.py\n+++ b/src/x.py\n@@ -1,0 +15,2 @@\n+print(1)\n+eval(user)\n'
  findings=self.p.review_diff(diff);self.assertEqual(findings[0].line,16)
 def test_syntax(self):
  self.assertTrue(any(x.rule=='syntax' for x in self.p.review_file('x.py','def bad(:\n')))
if __name__=='__main__':unittest.main()
