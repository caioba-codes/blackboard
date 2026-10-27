"""The source viewer: which files the bridge serves (only inside the course folder) and which links the board renders."""
import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bridge', ROOT / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
TMPL = (ROOT / 'board/board.html.tmpl').read_text()

LESSON = """---
title: Exam 2
---

::: sources
- The official [review](../sources/review/exam2.pdf) and `topics/numbers`.
- Old exams `exams2/missing-e9.pdf`.
:::

<!-- source: exams2/fa18-kj-s2 Problem 2, p.3 -->
Problem text.
"""


class SourceViewerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        course = Path(self.tmp.name) / 'ece'
        self.wsp = str(course / 'learn')
        src = course / 'learn' / 'sources'
        for rel, body in [('review/exam2.pdf', b'%PDF-1.4'), ('exams2/fa18-kj-s2.pdf', b'%PDF-1.4'),
                          ('exams2/fa18-kj-e2.pdf', b'%PDF-1.4'), ('exams2/fa18-kj-e2.pdf.txt', b'text'),
                          ('topics/numbers.txt', b'two\'s complement'), ('.hidden/secret.txt', b'no')]:
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            (src / rel).write_bytes(body)
        (course / 'learn' / 'lessons').mkdir(parents=True)
        self.lesson = course / 'learn' / 'lessons' / '0001-exam.md'
        self.lesson.write_text(LESSON)
        (course / 'grades.json').write_text('{}')
        outside = Path(self.tmp.name) / 'outside.pdf'
        outside.write_bytes(b'%PDF')
        os.symlink(outside, src / 'escape.pdf')

    def tearDown(self):
        self.tmp.cleanup()

    def test_serves_only_viewable_files_inside_the_course(self):
        ok = bridge.source_file('exams2/fa18-kj-e2.pdf', self.wsp)
        self.assertTrue(ok.endswith('sources/exams2/fa18-kj-e2.pdf'))
        self.assertTrue(bridge.source_file('../sources/review/exam2.pdf', self.wsp))
        self.assertTrue(bridge.source_file('fa18-kj-s2', self.wsp), 'a bare name is found anywhere in the course')
        for bad in ['../../outside.pdf', '../../../../etc/hosts', '/etc/hosts', '~/.zshrc', 'escape.pdf',
                    '.hidden/secret.txt', '../../grades.json', 'exams2/nope.pdf', '', 'a\0b.pdf']:
            self.assertIsNone(bridge.source_file(bad, self.wsp), bad)

    def test_extracted_text_opens_the_pdf(self):
        self.assertTrue(bridge.source_file('exams2/fa18-kj-e2.pdf.txt', self.wsp).endswith('fa18-kj-e2.pdf'))

    def test_cited_files_list_the_sources_block_comments_and_the_exam_beside_a_solution(self):
        files = bridge.cited_files(self.wsp, str(self.lesson), 'ece')
        found = {f['path']: f for f in files if f['found']}
        self.assertEqual(set(found), {'review/exam2.pdf', 'topics/numbers.txt', 'exams2/fa18-kj-e2.pdf', 'exams2/fa18-kj-s2.pdf'})
        self.assertEqual(found['exams2/fa18-kj-s2.pdf']['page'], 3)
        self.assertEqual(found['exams2/fa18-kj-s2.pdf']['url'], '/w/ece/source/learn/sources/exams2/fa18-kj-s2.pdf')
        self.assertEqual(found['topics/numbers.txt']['kind'], 'text')
        self.assertEqual([f['ref'] for f in files if not f['found']], ['exams2/missing-e9.pdf'])

    def test_chat_prompt_names_the_open_file(self):
        p = bridge.chat_prompt('0001', str(self.lesson), self.wsp, 'how do I start?', 'exams2/fa18-kj-e2.pdf, page 3')
        self.assertIn('[Viewing: the user has exams2/fa18-kj-e2.pdf, page 3 open', p)
        self.assertNotIn('Viewing', bridge.chat_prompt('0001', str(self.lesson), self.wsp, 'hi'))

    def test_board_links_sources_and_chat_citations(self):
        self.assertIn('id="srcview"', TMPL)
        self.assertIn('srcFiles()', TMPL)
        self.assertIn('viewing:srcViewing()', TMPL)
        self.assertIn('not found on this Mac', TMPL)
        cite = re.compile(re.search(r"const CITE=/(.+)/g;", TMPL).group(1).replace('\\/', '/'))
        said = 'The answer is in `exams2/fa18-kj-s2.pdf`, page 1, and sources/review/exam2-2026-1019.txt; see fa21-kj-e2 too.'
        self.assertEqual(cite.findall(said), ['exams2/fa18-kj-s2.pdf', 'sources/review/exam2-2026-1019.txt'])
        self.assertEqual(cite.findall('see exams2/fa21-kj-e2 now'), ['exams2/fa21-kj-e2'])


if __name__ == '__main__':
    unittest.main()
