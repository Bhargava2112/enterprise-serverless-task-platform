import unittest
from app import VisualInspector,features,ImageError,read_pgm
GOOD=[[235]*8 for _ in range(8)]
BAD=[[235]*8 for _ in range(8)]
for r in range(2,6):
 for c in range(2,6):BAD[r][c]=10
class VisionTests(unittest.TestCase):
 def test_features(self):
  self.assertEqual(features(GOOD)[2],0)
  self.assertGreater(features(BAD)[2],0)
 def test_train_serialize(self):
  data=[(GOOD,0),(BAD,1)]*5
  m=VisualInspector(.5);m.fit(data);copy=VisualInspector.from_json(m.to_json())
  self.assertEqual(copy.classify(BAD),m.classify(BAD))
  self.assertGreater(m.classify(BAD)['defect_probability'],m.classify(GOOD)['defect_probability'])
 def test_image_validation(self):
  with self.assertRaises(ImageError):features([[1,2],[3]])
  with self.assertRaises(ImageError):features([[500]])
 def test_pgm_parser(self):
  self.assertEqual(read_pgm('P2\n2 2\n255\n0 1 2 3'),[[0,1],[2,3]])
  with self.assertRaises(ImageError):read_pgm('P5 2 2 255 0')
if __name__=='__main__':unittest.main()
