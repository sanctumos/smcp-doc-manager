"""
Convert markdown to PDF or DOCX.
- PDF: markdown-pdf (pure Python, PyMuPDF).
- DOCX: pypandoc (requires pandoc installed).
"""

import os
import tempfile
from typing import Any


def markdown_to_pdf(markdown_content: str, title: str | None = None) -> dict[str, Any]:
    """Convert markdown string to PDF bytes. Returns {status, pdf_bytes|error}."""
    try:
        from markdown_pdf import MarkdownPdf, Section
    except ImportError:
        return {"status": "error", "error": "markdown-pdf not installed. pip install markdown-pdf"}

    try:
        pdf = MarkdownPdf(toc_level=2, optimize=True)
        if title:
            pdf.meta["title"] = title
        pdf.add_section(Section(markdown_content))
        import io
        buf = io.BytesIO()
        pdf.save_bytes(buf)
        return {"status": "success", "pdf_bytes": buf.getvalue()}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def markdown_to_docx(markdown_content: str) -> dict[str, Any]:
    """Convert markdown string to DOCX bytes. Returns {status, docx_bytes|error}. Requires pandoc."""
    try:
        import pypandoc
    except ImportError:
        return {"status": "error", "error": "pypandoc not installed. pip install pypandoc. Pandoc must also be installed on the system."}

    md_path = None
    docx_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            f.write(markdown_content.encode("utf-8"))
            md_path = f.name
        docx_path = tempfile.mktemp(suffix=".docx")
        pypandoc.convert_file(md_path, "docx", outputfile=docx_path)
        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        return {"status": "success", "docx_bytes": docx_bytes}
    except FileNotFoundError:
        return {"status": "error", "error": "Pandoc not found. Install pandoc (e.g. apt install pandoc or download from pandoc.org)."}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        if md_path and os.path.exists(md_path):
            try:
                os.unlink(md_path)
            except Exception:
                pass
        if docx_path and os.path.exists(docx_path):
            try:
                os.unlink(docx_path)
            except Exception:
                pass
