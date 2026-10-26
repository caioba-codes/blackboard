import importlib.util
from pathlib import Path
import re
import unittest

BIN = Path(__file__).resolve().parents[1] / 'bin'
spec = importlib.util.spec_from_file_location('relevance', BIN / 'relevance.py')
rel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rel)

class RelevanceTests(unittest.TestCase):
    def test_literal_keyword_hits_are_rejected(self):
        # Real off-topic picks the old substring/any-word scoring accepted.
        for query, title in [
            ('calculus textbook page with integral formulas', 'Sharp DR 90 Nemesis racing airplane (page 1)'),
            ('handwritten math formula sheet', 'Irish Medicines Formulary book cover'),
            ('chalkboard with mathematical formulas', 'Fuji TV Building'),
            ('chalk sticks on a slate board', 'Electronic Circuit Board'),
            ('folded paper crease, macro', 'Origami Trash'),
        ]:
            self.assertIsNone(rel.score(query, title), (query, title))

    def test_whole_words_plurals_and_camel_case(self):
        self.assertNotIn('formula', rel.words('Formulary'))
        self.assertEqual(rel.score('integral calculus handwriting', 'File:IntegralCalculus_handwriting.jpg'), ['integral', 'calculu', 'handwriting'])
        self.assertEqual(rel.score('Java source code on a computer screen', 'Java_source_code.png'), ['java', 'source', 'code'])
        self.assertEqual(rel.score('sorted integers', 'An integer sorting'), None)  # 'sorted' is not 'sorting'
        self.assertEqual(rel.hits('intégrale neige', 'Une intégrale tracée dans la neige'), ['intégrale', 'neige'])

    def test_generic_words_count_only_when_alone(self):
        self.assertEqual(rel.terms('handwritten formula sheet on a desk, close up'), ['handwritten'])
        self.assertEqual(rel.terms('paper page macro'), ['paper', 'page', 'macro'])
        self.assertEqual(rel.score('graph of a function', 'Graph of a function'), ['function'])

    def test_board_photos_only_for_board_subjects(self):
        self.assertIsNone(rel.score('mathematical formulas handwritten', 'Mathematical formulas handwritten on a blackboard'))
        self.assertEqual(rel.score('school blackboard', 'Old school blackboard'), ['school', 'blackboard'])

    def test_title_hits_rank_first(self):
        q = 'area between curves integral'
        museum = rel.score(q, 'Late Medieval Mount', 'area between ... curved ... integral part of the mount')
        graph = rel.score(q, 'Center of mass using integral', 'area under a curve')
        self.assertLess(rel.rank_key(q, 'Center of mass using integral', graph), rel.rank_key(q, 'Late Medieval Mount', museum))

    def test_image_sh_python_compiles(self):
        src = (BIN / 'image.sh').read_text()
        body = re.search(r"<<'PY'\n(.*)\nPY\n", src, re.S)[1]
        compile(body, 'image.sh', 'exec')
        self.assertIn('from relevance import score', body)

if __name__ == '__main__':
    unittest.main()
