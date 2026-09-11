import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(n,r):
 p=ROOT/r;s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
s=load('strategy_149_163','strategy/engines.py')
class T(unittest.TestCase):
 def test_149_strategy_major_decision_stays_human(self):
  x=s.StrategicOption('a',10,2,.9,('e',));self.assertEqual(('HUMAN_REQUIRED','a'),s.strategy_recommend((x,)))
 def test_150_forecast(self):self.assertEqual((4.0,5.0),s.simple_forecast((1,2,3),2))
 def test_151_capacity(self):self.assertEqual(('SCALE_REQUIRED',2.0),s.CapacitySignal(10,10,.2).status())
 def test_152_opportunity(self):
  self.assertEqual(('MVP','o'),s.Opportunity('o',10,2,1,'e').decision(5));self.assertEqual(('HUMAN_REQUIRED','MONEY_LIMIT'),s.Opportunity('o',10,6,1,'e').decision(5))
 def test_153_innovation(self):self.assertTrue(s.InnovationHypothesis('h',10,8,0,'e').worthwhile)
 def test_154_experiment(self):self.assertEqual('SCALE',s.ExperimentResult('x',(1,1),(2,2),.5,'e').decision())
 def test_155_trading_lab_real_execution_blocked(self):self.assertEqual(('BLOCKED','HIGH_RISK'),s.LabRun('LAB-TRD','PAPER',True,'paper',0,0,'e').decision())
 def test_156_seo_lab(self):self.assertEqual(('GREEN',None),s.LabRun('LAB-SEO','LAB',False,'staging',0,0,'e').decision())
 def test_157_marketing_lab_budget(self):self.assertEqual(('HUMAN_REQUIRED','MONEY_LIMIT'),s.LabRun('LAB-MKT','LAB',False,'test',2,1,'e').decision())
 def test_158_ai_lab(self):self.assertEqual(('GREEN',None),s.LabRun('LAB-AI','LAB',False,'synthetic',0,0,'e').decision())
 def test_159_automation_lab(self):self.assertEqual(('GREEN',None),s.LabRun('LAB-AUT','PREPROD',False,'fixtures',0,0,'e').decision())
 def test_160_market_intelligence(self):
  self.assertEqual('GREEN',s.market_intelligence((s.MarketSignal('rate',2,'official',.9),))[0]);self.assertEqual('HUMAN_REQUIRED',s.market_intelligence((s.MarketSignal('rate',2,'x',.2),))[0])
 def test_161_expansion(self):
  rows=(s.CityScore('A',10,2,5,5,2,5),s.CityScore('B',5,4,5,5,4,5));w={'demand':1,'competition':1,'partner_fit':1,'seo':1,'cost':1,'capacity':1};self.assertEqual(('A','B'),s.rank_cities(rows,w))
 def test_162_franchise(self):self.assertTrue(s.ReplicationReadiness(True,True,True,True,'cfg').green)
 def test_163_venture(self):
  self.assertEqual(('SCALE',None),s.VentureCase('x',True,True,1,True,0,0).decision());self.assertEqual(('HUMAN_REQUIRED','MONEY_LIMIT'),s.VentureCase('x',True,True,1,True,2,1).decision())
if __name__=='__main__':unittest.main()
