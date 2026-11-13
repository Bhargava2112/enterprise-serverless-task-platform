import unittest
from app import Ledger,Conflict,InsufficientFunds
class LedgerTests(unittest.TestCase):
 def setUp(self):self.l=Ledger();self.l.open_account('alice',1000);self.l.open_account('bob',100)
 def test_double_entry_and_balances(self):
  self.l.transfer('alice','bob',250,'k1')
  self.assertEqual(self.l.balance('alice'),750)
  self.assertEqual(self.l.balance('bob'),350)
  self.assertEqual(self.l.verify(),{'valid':True,'entries':2})
 def test_idempotency(self):
  self.assertFalse(self.l.transfer('alice','bob',100,'same')['replay'])
  self.assertTrue(self.l.transfer('alice','bob',100,'same')['replay'])
  self.assertEqual(self.l.balance('alice'),900)
  with self.assertRaises(Conflict):self.l.transfer('alice','bob',50,'same')
 def test_insufficient_funds_atomic(self):
  with self.assertRaises(InsufficientFunds):self.l.transfer('alice','bob',5000,'large')
  self.assertEqual((self.l.balance('alice'),self.l.balance('bob')),(1000,100))
 def test_invalid(self):
  with self.assertRaises(ValueError):self.l.transfer('alice','alice',50,'k')
  with self.assertRaises(KeyError):self.l.transfer('alice','missing',20,'k')
if __name__=='__main__':unittest.main()
