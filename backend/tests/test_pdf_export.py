import builtins
import io
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PyPDF2 import PdfReader

from backend.api.auth import get_current_user
from backend.api.routes import router
from backend.services import pdf_export


SAMPLE_ANALYSIS = {
    'ATS_score': 72,
    'ats_score': 72,
    'component_scores': {
        'formatting': 15, 'keywords': 18, 'content': 19,
        'skill_validation': 10, 'ats_compatibility': 10,
    },
    'issues_summary': ['Add measurable achievements'],
    'detailed_feedback': [{
        'issue_title': 'Add measurable achievements',
        'severity_level': 'high',
        'ats_impact': 'Makes experience more specific.',
        'explanation': 'The experience section lists duties without outcomes.',
        'where_it_appears': 'Experience',
        'how_to_fix': 'Describe the result of each project using accurate metrics.',
        'action_items': ['Review each experience bullet.', 'Add a measurable result.'],
        'example_improvement': 'Reduced report processing time by 25%.',
    }],
    'interpretation': 'Sample report for PDF export verification.',
    'strengths': ['Clear work history and readable section headings.'],
    'skill_validation_details': {
        'validated': [{'skill': 'Python', 'projects': ['Resume analysis API']}],
        'unvalidated': ['Docker'], 'total': 2, 'validated_count': 1,
        'validation_pct': 50,
    },
    'jd_match_analysis': {
        'match_percentage': 70, 'semantic_similarity': 0.75,
        'matched_keywords': ['Python', 'FastAPI'],
        'missing_keywords': ['Docker'], 'skills_gap': ['Container deployment'],
    },
}


class PDFExportTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: 'test-user'
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_native_import_failure_has_setup_instructions(self):
        original_import = builtins.__import__

        def import_without_weasyprint(name, *args, **kwargs):
            if name == 'weasyprint':
                raise OSError("cannot load library 'libgobject-2.0-0'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=import_without_weasyprint):
            with self.assertRaisesRegex(pdf_export.PDFUnavailableError, 'Pango'):
                pdf_export.generate_combined_pdf({'sample': '<p>Test</p>'})

    def test_empty_reports_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'At least one'):
            pdf_export.generate_combined_pdf({})

    def test_missing_renderer_returns_503_for_current_report(self):
        with patch.object(pdf_export, '_load_html_renderer',
                          side_effect=pdf_export.PDFUnavailableError('Install Pango runtime')):
            response = self.client.post('/api/v1/generate-pdf', json=SAMPLE_ANALYSIS)
        self.assertEqual(response.status_code, 503)
        self.assertIn('Pango', response.json()['detail'])

    def test_missing_renderer_returns_503_for_history_report(self):
        history = [{'id': 'sample', 'analysis_result': SAMPLE_ANALYSIS}]
        with patch('backend.database.supabase_db.get_user_history',
                   new_callable=AsyncMock, return_value=history), \
             patch.object(pdf_export, '_load_html_renderer',
                          side_effect=pdf_export.PDFUnavailableError('Install Pango runtime')):
            response = self.client.get('/api/v1/history/sample/pdf')
        self.assertEqual(response.status_code, 503)
        self.assertIn('Pango', response.json()['detail'])

    def test_real_renderer_merges_reports_in_order(self):
        result = pdf_export.generate_combined_pdf({
            'first': '<h1>First report</h1>',
            'second': '<h1>Second report</h1>',
        })
        reader = PdfReader(io.BytesIO(result))
        self.assertEqual(len(reader.pages), 2)
        self.assertIn('First report', reader.pages[0].extract_text())
        self.assertIn('Second report', reader.pages[1].extract_text())

    def test_current_report_endpoint_returns_readable_pdf(self):
        response = self.client.post('/api/v1/generate-pdf', json=SAMPLE_ANALYSIS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/pdf')
        self.assertIn('attachment;', response.headers['content-disposition'])
        reader = PdfReader(io.BytesIO(response.content))
        self.assertGreaterEqual(len(reader.pages), 4)
        self.assertIn('72', reader.pages[0].extract_text())

    def test_history_report_endpoint_returns_readable_pdf(self):
        history = [{'id': 'sample', 'analysis_result': SAMPLE_ANALYSIS}]
        with patch('backend.database.supabase_db.get_user_history',
                   new_callable=AsyncMock, return_value=history) as get_history:
            response = self.client.get('/api/v1/history/sample/pdf')
        get_history.assert_awaited_once_with('test-user')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF-'))


if __name__ == '__main__':
    unittest.main()
