import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from groq import NotFoundError

from backend.services import groq_parser


class GroqParserTests(unittest.TestCase):
    def test_valid_resume_json_does_not_retry(self):
        with patch.object(groq_parser, '_get_client'), patch.object(
            groq_parser, '_call_groq', return_value='{"name":"Test User","skills":["Python"]}'
        ) as call:
            result = groq_parser.parse_resume('Synthetic resume')
        self.assertEqual(result['skills'], ['Python'])
        self.assertEqual(result['experience'], [])
        self.assertEqual(call.call_count, 1)

    def test_invalid_resume_json_retries(self):
        with patch.object(groq_parser, '_get_client'), patch.object(
            groq_parser, '_call_groq', side_effect=['invalid', '{"name":"Test User"}']
        ) as call:
            result = groq_parser.parse_resume('Synthetic resume')
        self.assertEqual(result['name'], 'Test User')
        self.assertEqual(call.call_count, 2)

    def test_non_object_responses_fail_after_retry(self):
        for parser in (groq_parser.parse_resume, groq_parser.parse_job_description):
            with self.subTest(parser=parser.__name__):
                with patch.object(groq_parser, '_get_client'), patch.object(
                    groq_parser, '_call_groq', side_effect=['[]', 'null']
                ) as call:
                    with self.assertRaisesRegex(ValueError, 'unparseable response'):
                        parser('Synthetic text')
                self.assertEqual(call.call_count, 2)

    def test_model_configuration_is_used(self):
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))]
        )
        with patch.object(groq_parser, 'GROQ_MODEL', 'configured-model'):
            self.assertEqual(groq_parser._call_groq(client, 'JSON system', 'JSON user'), '{}')
        self.assertEqual(client.chat.completions.create.call_args.kwargs['model'], 'configured-model')

    def test_missing_model_has_actionable_error(self):
        client = Mock()
        response = httpx.Response(404, request=httpx.Request('POST', 'https://api.groq.com'))
        client.chat.completions.create.side_effect = NotFoundError(
            'model_not_found', response=response, body={'error': {'code': 'model_not_found'}}
        )
        with self.assertRaisesRegex(ValueError, 'Set GROQ_MODEL in backend/.env'):
            groq_parser._call_groq(client, 'JSON system', 'JSON user')


if __name__ == '__main__':
    unittest.main()
