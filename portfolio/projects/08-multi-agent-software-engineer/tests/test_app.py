import unittest
from app import EngineeringWorkflow,WorkflowError,AuditLog,safe_path
class AgentTests(unittest.TestCase):
 def make(self):return EngineeringWorkflow(lambda req:{'path':'src/module.py','content':'x = 1\n'},lambda q,p:'accept')
 def test_human_gate(self):
  w=self.make();w.schedule('design','write module');self.assertEqual(w.advance('design'),'awaiting-human')
  self.assertEqual(w.report()['states']['design'],'awaiting-human')
  self.assertIn('content',w.human_approve('design',True));self.assertTrue(w.audit.verify())
 def test_dependencies(self):
  w=self.make();w.schedule('a','a');w.schedule('b','b',['a'])
  with self.assertRaises(WorkflowError):w.advance('b')
  w.advance('a');w.human_approve('a',True);w.advance('b');self.assertEqual(w.tasks['b'].status,'awaiting-human')
 def test_reject_paths(self):
  for path in ['../outside','.ssh/id_rsa','/tmp/evil','src\\bad']:
   with self.assertRaises(WorkflowError):safe_path(path)
 def test_budgets_and_secrets(self):
  w=EngineeringWorkflow(lambda q:{'path':'src/x','content':'aws_secret_access_key=123'},lambda q,p:'accept')
  w.schedule('t','task')
  with self.assertRaises(WorkflowError):w.advance('t')
 def test_log_tamper(self):
  w=self.make();w.schedule('t','task');w.audit.events[0]['action']='changed';self.assertFalse(w.audit.verify())
if __name__=='__main__':unittest.main()
