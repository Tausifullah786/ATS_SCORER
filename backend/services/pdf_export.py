import os
from pathlib import Path


PRINT_CSS = '''
    @page { size: A4; margin: 16mm; }
    body { padding: 0 !important; }
    h1, h2, h3 { break-after: avoid; }
    .info-block, .stats-bar, .validated-skill, .issue-card { break-inside: avoid; }
    .footer { break-before: avoid; break-inside: avoid; }
'''


class PDFUnavailableError(RuntimeError):
    """The PDF renderer or one of its native dependencies is unavailable."""


def _load_html_renderer():
    # WeasyPrint needs Pango DLLs on Windows in addition to its pip package.
    # Keep an explicitly configured DLL directory authoritative.
    if os.name == 'nt' and not os.environ.get('WEASYPRINT_DLL_DIRECTORIES'):
        for directory in (Path('C:/msys64/ucrt64/bin'), Path('C:/msys64/mingw64/bin')):
            if (directory / 'libgobject-2.0-0.dll').is_file():
                os.environ['WEASYPRINT_DLL_DIRECTORIES'] = str(directory)
                break
    try:
        from weasyprint import HTML, CSS
    except (ImportError, OSError) as exc:
        raise PDFUnavailableError(
            'PDF generation requires WeasyPrint and its Pango runtime. '
            'See the PDF setup section in README.md, then restart the backend.'
        ) from exc
    return HTML, CSS


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not html_docs:
        raise ValueError('At least one HTML report is required.')
    HTML, CSS = _load_html_renderer()
    print_styles = CSS(string=PRINT_CSS)
    documents = []
    
    # Render each report in insertion order, starting each on a new page.
    for html_str in html_docs.values():
        doc = HTML(string=html_str).render(stylesheets=[print_styles])
        documents.append(doc)
    
    # Merge them into the first document
    first_doc = documents[0]
    for other_doc in documents[1:]:
        for page in other_doc.pages:
            first_doc.pages.append(page)
            
    # Write combined PDF bytes
    pdf_bytes = first_doc.write_pdf()
    return pdf_bytes
