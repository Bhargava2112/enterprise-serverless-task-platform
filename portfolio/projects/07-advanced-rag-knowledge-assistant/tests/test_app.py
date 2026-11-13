import unittest
from app import GroundedAssistant,Index,retrieval_recall_at_k
class RAGTests(unittest.TestCase):
 def setUp(self):
  self.i=Index();self.i.add('d1','Database replicas require an LSN checkpoint and lag monitoring.',tenant='A',source='db.md')
  self.i.add('d2','Customer support tickets route to the on-call lead.',tenant='A',source='support.md')
  self.i.add('private','Secret replication passwords in internal vault.',tenant='B',source='secrets.md')
 def test_retrieval_and_citations(self):
  h=self.i.search('database replica lag',tenant='A')
  self.assertEqual(h[0]['doc_id'],'d1')
  self.assertEqual(retrieval_recall_at_k(self.i,[('database replica','d1')],tenant='A'),1)
 def test_tenant_and_source_acl(self):
  self.assertFalse(self.i.search('passwords',tenant='A'))
  self.assertFalse(self.i.search('database',tenant='A',allowed_sources={'support.md'}))
 def test_abstains(self):
  self.assertFalse(GroundedAssistant(self.i).answer('nonexistent-phrase',tenant='A')['grounded'])
 def test_generator_must_return_valid_citations(self):
  assistant=GroundedAssistant(self.i,lambda q,c:{'answer':'Replica lag must be monitored.', 'citations':[c[0]['id']]})
  self.assertTrue(assistant.answer('replica lag',tenant='A')['grounded'])
  bad=GroundedAssistant(self.i,lambda q,c:{'answer':'bad','citations':['fabricated']})
  with self.assertRaises(ValueError):bad.answer('replica lag',tenant='A')
 def test_deduplication(self):
  self.i.add('d1','Database replicas require an LSN checkpoint and lag monitoring.',tenant='A',source='db.md')
  self.assertEqual(len(self.i.chunks),3)
if __name__=='__main__':unittest.main()
