"""Regression checks for strict previews and a byte-pinned published PDF."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import build_release


class PdfPublicationTests(unittest.TestCase):
    def test_current_pdf_requires_matching_source(self):
        pdf = SimpleNamespace(metadata=SimpleNamespace(subject='sha256: current-source'))
        self.assertEqual(build_release.verify_pdf_version(Path('/unused'), pdf, 'current-source', {}), 'current')

    def test_retained_pdf_requires_correct_path_and_bytes(self):
        with TemporaryDirectory() as folder:
            published = Path(folder) / 'published.pdf'
            preview = Path(folder) / 'preview.pdf'
            published.write_bytes(b'previous publication')
            preview.write_bytes(published.read_bytes())
            meta = {'published_pdf': {'version': '1.21.0', 'sha256': hashlib.sha256(published.read_bytes()).hexdigest()}}
            pdf = SimpleNamespace(metadata=SimpleNamespace(subject='previous-source'))
            with patch.object(build_release, 'PUBLISHED_PDF', published):
                self.assertEqual(build_release.verify_pdf_version(published, pdf, 'current-source', meta), 'preserved')
                with self.assertRaisesRegex(ValueError, '正文指纹'):
                    build_release.verify_pdf_version(preview, pdf, 'current-source', meta)
                with self.assertRaisesRegex(ValueError, '正文指纹'):
                    build_release.verify_pdf_version(published, pdf, 'current-source', {})
                published.write_bytes(b'changed publication')
                with self.assertRaisesRegex(ValueError, '已发布 PDF 指纹'):
                    build_release.verify_pdf_version(published, pdf, 'current-source', meta)
                pdf.metadata.subject = 'current-source'
                with self.assertRaisesRegex(ValueError, '已发布 PDF 指纹'):
                    build_release.verify_pdf_version(published, pdf, 'current-source', meta)


if __name__ == '__main__':
    unittest.main()
