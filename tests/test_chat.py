import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[1] / 'board/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def text_start():
    return {'type': 'stream_event', 'event': {'type': 'content_block_start', 'content_block': {'type': 'text', 'text': ''}}}


def text_delta(t):
    return {'type': 'stream_event', 'event': {'type': 'content_block_delta', 'delta': {'type': 'text_delta', 'text': t}}}


class ChatStreamTests(unittest.TestCase):
    def test_stream_json_becomes_steps_deltas_and_a_saved_end(self):
        turn = bridge.Turn(proc=None, wsp='/ws/learn')
        lines = [
            {'type': 'system', 'subtype': 'init', 'session_id': 's-1'},
            text_start(), text_delta('Let me read it.'),
            {'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': '/ws/learn/sources/hw1.txt', 'pages': '2'}}]}},
            {'type': 'assistant', 'message': {'content': [
                {'type': 'tool_use', 'name': 'WebSearch', 'input': {'query': 'power rule'}}]}},
            text_start(), text_delta('The answer'), text_delta(' is $9$.'),
            {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'The answer is $9$.'},
        ]
        events = [e for line in lines for e in turn.feed(line)]
        self.assertEqual(events, [
            ('delta', {'text': 'Let me read it.'}),
            ('step', {'tool': 'Read', 'label': 'Reading sources/hw1.txt, pages 2'}),
            ('step', {'tool': 'WebSearch', 'label': 'Searching the web: power rule'}),
            ('delta', {'text': '\n\n'}),
            ('delta', {'text': 'The answer'}),
            ('delta', {'text': ' is $9$.'}),
        ])
        self.assertEqual(turn.text, 'Let me read it.\n\nThe answer is $9$.')
        self.assertEqual(turn.session_id, 's-1')
        self.assertEqual(turn.end, ('done', {}))

    def test_error_result_ends_the_turn_with_its_message(self):
        turn = bridge.Turn(proc=None, wsp='/ws/learn')
        self.assertEqual(turn.feed({'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'result': 'rate limited'}), [])
        self.assertEqual(turn.end, ('error', {'message': 'rate limited'}))


class LessonSourcesTests(unittest.TestCase):
    def test_sources_section_and_resources_resolve_to_files_and_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            course = Path(tmp) / 'math'
            ws = course / 'learn'
            (ws / 'lessons').mkdir(parents=True)
            (ws / 'sources/hw').mkdir(parents=True)
            (course / 'reference').mkdir()
            (ws / 'sources/hw/hw1.txt').write_text('Problem 3. Use the power rule.\n')
            (course / 'reference/notes.md').write_text('plus C\n')
            (ws / 'RESOURCES.md').write_text('- [Homework 1](sources/hw/hw1.txt)\n- [Slides](sources/missing.pdf)\n')
            lesson = ws / 'lessons/0001-power-rule.md'
            lesson.write_text('---\ntitle: Power Rule\n---\n\n## Rule\n\nUse `javac`.\n\n## Sources\n'
                              '- Homework 1, problem 3 (`hw1.txt`)\n'
                              '- Notes (`../reference/notes.md`)\n'
                              '- https://example.org/power-rule\n')
            sources, cited = bridge.lesson_sources(str(ws), str(lesson))
            self.assertEqual(sources, [str(ws / 'sources/hw/hw1.txt'), str(course / 'reference/notes.md'),
                                       'https://example.org/power-rule'])
            self.assertEqual(cited, '- Homework 1, problem 3 (`hw1.txt`)\n- Notes (`../reference/notes.md`)\n'
                                    '- https://example.org/power-rule')


    def test_sources_dropdown_block_with_paths_in_a_comment(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / 'learn'
            (ws / 'lessons').mkdir(parents=True); (ws / 'sources').mkdir()
            (ws / 'sources/exam.txt').write_text('Q1\n')
            lesson = ws / 'lessons/0001-x.md'
            lesson.write_text('---\ntitle: X\n---\n\n::: sources\n<!-- files: `sources/exam.txt` -->\n- Fall 2017 Exam 2 · worked examples\n:::\n\n## Chapter 1 · A\n')
            sources, cited = bridge.lesson_sources(str(ws), str(lesson))
            self.assertEqual(sources, [str(ws / 'sources/exam.txt')])
            self.assertIn('Fall 2017 Exam 2', cited)


if __name__ == '__main__':
    unittest.main()


class ChatImageTests(unittest.TestCase):
    PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

    def test_images_are_saved_and_sent_as_image_blocks(self):
        with tempfile.TemporaryDirectory() as ws:
            blocks, names = bridge.chat_images(ws, '0011', [{'type': 'image/png', 'data': self.PNG}])
            self.assertEqual(blocks, [('image/png', self.PNG)])
            self.assertRegex(names[0], r'^0011-[0-9a-f]{12}\.png$')
            self.assertTrue((Path(ws) / 'reference/chat/img' / names[0]).is_file())
            msg = __import__('json').loads(bridge.chat_input('hi', blocks))
            content = msg['message']['content']
            self.assertEqual([c['type'] for c in content], ['image', 'text'])
            self.assertEqual(content[0]['source']['media_type'], 'image/png')

    def test_bad_images_are_refused(self):
        with tempfile.TemporaryDirectory() as ws:
            self.assertIsInstance(bridge.chat_images(ws, '0001', [{'type': 'image/svg+xml', 'data': self.PNG}]), str)
            self.assertIsInstance(bridge.chat_images(ws, '0001', [{'type': 'image/png', 'data': 'not base64!'}]), str)
            self.assertIsInstance(bridge.chat_images(ws, '0001', [{'type': 'image/png', 'data': self.PNG}] * 7), str)

    def test_the_turn_goes_in_as_stream_json(self):
        cmd = bridge.chat_command('s-1', False, 'WebSearch')
        self.assertEqual(cmd[cmd.index('--input-format') + 1], 'stream-json')
