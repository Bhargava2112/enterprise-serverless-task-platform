import hashlib,json,tempfile,unittest
from app import LogisticModel,Registry,SchemaError,evaluate,stratified_split,population_stability_index
SAMPLE=[{'throughput':i,'error_rate':i/100,'queue_depth':i//2,'label':int(i>=15)} for i in range(30)]
class MLOpsTests(unittest.TestCase):
 def test_reproducible_training(self):
  train,test=stratified_split(SAMPLE)
  a=LogisticModel.train(train);b=LogisticModel.train(train)
  self.assertEqual(a.serialize(),b.serialize())
  self.assertGreaterEqual(evaluate(a,test)['accuracy'],.7)
 def test_registry_promote(self):
  train,test=stratified_split(SAMPLE);model=LogisticModel.train(train)
  with tempfile.TemporaryDirectory() as d:
   reg=Registry(d);key=reg.register(model,evaluate(model,test),'abc123')
   reg.promote(key,min_accuracy=.7)
   self.assertAlmostEqual(reg.production().predict_proba(SAMPLE[0]),model.predict_proba(SAMPLE[0]))
 def test_gate_rejects_poor_model(self):
  with tempfile.TemporaryDirectory() as d:
   r=Registry(d);key=r.register(LogisticModel(),{'accuracy':.2},'abc')
   with self.assertRaises(ValueError):r.promote(key)
 def test_schema(self):
  with self.assertRaises(SchemaError):LogisticModel().predict_proba({'throughput':'NaN'})
 def test_drift(self):
  self.assertAlmostEqual(population_stability_index([.1,.2,.3],[.1,.2,.3]),0)
  self.assertGreater(population_stability_index([.1]*10,[10.]*10),.5)
if __name__=='__main__':unittest.main()
