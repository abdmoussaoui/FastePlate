import unittest,tempfile,pathlib,csv,json
from fasteplate.formatting import normalize,physical_order
from fasteplate.results import Token
from fasteplate.preprocessing import prepare
import numpy as np
class TextTests(unittest.TestCase):
 def test_unicode_preserves_letters(self):
  self.assertEqual(normalize('٩٠٧٤٣\u200f ب ۲۶'),'90743 ب 26')
  self.assertNotEqual(normalize('أ'),normalize('ا'))
 def test_physical_order_and_lines(self):
  def token(x,y,text): return Token([[x,y],[x+20,y],[x+20,y+15],[x,y+15]],text,.9)
  self.assertEqual(physical_order([token(80,0,'26'),token(0,0,'90743'),token(50,0,'ب'),token(0,40,'WW')]),'90743 ب 26\nWW')
 def test_small_crops_and_modes(self):
  crop=np.full((8,30,3),240,dtype=np.uint8)
  for mode in ['color','resize','contrast','threshold','perspective','legacy-main','legacy-main2']:
   self.assertTrue(prepare(crop,mode).size)
  with self.assertRaises(ValueError): prepare(crop,'unknown')
if __name__=='__main__': unittest.main()
