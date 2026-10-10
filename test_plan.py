import os, unittest
from unittest.mock import patch
from server import plan
class PlanTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'GROCERY_PROVIDER_URL':''});self.env.start();self.addCleanup(self.env.stop)
    def test_scaling_and_aggregation(self):
        p=plan(dict(category='Keto',people=3,days=3,location='30101'))
        chicken=next(i for i in p['shopping'] if i['name']=='Chicken breast')
        self.assertEqual(chicken['quantity'],1200)
        self.assertEqual(len(p['meals']),3)
        self.assertEqual(len(p['stores']),3)
        self.assertEqual(p['mode'],'demo')
    def test_all_categories(self):
        for category in ['Keto','Vegan','High Protein','Affordable']:
            self.assertEqual(len(plan(dict(category=category,people=1,days=31,location='30101'))['meals']),31)
    def test_invalid_input(self):
        for changes in [dict(people=0),dict(days=32),dict(people=1.5),dict(people=True),dict(location=''),dict(category='Other')]:
            with self.assertRaises(ValueError): plan(dict(dict(category='Keto',people=2,days=7,location='30101'),**changes))
if __name__=='__main__': unittest.main()
