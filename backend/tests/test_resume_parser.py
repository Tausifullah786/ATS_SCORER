import io
import unittest
import zipfile
from unittest.mock import patch

from docx import Document

from backend.services.resume_parser import (
    FileParsingError,
    FileValidationError,
    parse_resume_file,
    validate_file,
)


def make_pdf():
    """Build a minimal text PDF with a valid cross-reference table."""
    stream = b'BT /F1 12 Tf 72 720 Td (Python developer resume) Tj ET'
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
    ]
    data = bytearray(b'%PDF-1.4\n')
    offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f'{number} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = len(data)
    data.extend(b'xref\n0 6\n0000000000 65535 f \n')
    for offset in offsets:
        data.extend(f'{offset:010} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return bytes(data)


class ResumeParserTests(unittest.TestCase):
    def test_pdf_text_extraction(self):
        text, metadata = parse_resume_file(make_pdf(), 'resume.pdf')
        self.assertIn('Python developer resume', text)
        self.assertEqual(metadata['file_type'], 'pdf')

    def test_docx_text_extraction_without_relying_on_extension(self):
        document = Document()
        document.add_paragraph('Python developer resume')
        buffer = io.BytesIO()
        document.save(buffer)
        text, metadata = parse_resume_file(buffer.getvalue(), 'upload.bin')
        self.assertIn('Python developer resume', text)
        self.assertEqual(metadata['file_type'], 'docx')

    def test_empty_file_is_a_validation_error(self):
        self.assertEqual(len(validate_file(b'', 'resume.pdf')), 3)
        with self.assertRaisesRegex(FileValidationError, 'empty'):
            parse_resume_file(b'', 'resume.pdf')

    def test_oversized_upload_is_rejected(self):
        with patch('backend.services.resume_parser.MAX_FILE_SIZE_BYTES', 4):
            self.assertFalse(validate_file(b'%PDF-1.4', 'resume.pdf')[0])

    def test_renamed_text_file_is_rejected(self):
        self.assertFalse(validate_file(b'Not a PDF', 'resume.pdf')[0])

    def test_generic_zip_is_not_a_docx(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('resume.txt', 'Python developer')
        self.assertFalse(validate_file(buffer.getvalue(), 'resume.docx')[0])

    def test_corrupted_pdf_is_rejected_by_parser(self):
        with self.assertRaises(FileParsingError):
            parse_resume_file(b'%PDF-1.4\ncorrupted', 'resume.pdf')

    def test_legacy_doc_requests_conversion(self):
        with self.assertRaisesRegex(FileParsingError, 'convert'):
            parse_resume_file(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', 'resume.doc')


if __name__ == '__main__':
    unittest.main()
