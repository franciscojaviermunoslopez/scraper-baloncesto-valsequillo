# test_telegram_bot.py
import fitz
import pytest


def crear_pdf_minimo():
    """Crea un PDF mínimo en memoria para tests."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Test PDF Valsequillo", fontsize=12)
    return doc.tobytes()


class TestPdfAImagen:
    def test_retorna_bytes_png(self, tmp_path):
        """pdf_a_imagen devuelve bytes no vacíos."""
        from telegram_bot import pdf_a_imagen

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(crear_pdf_minimo())

        resultado = pdf_a_imagen(str(pdf_path))

        assert isinstance(resultado, bytes)
        assert len(resultado) > 0

    def test_png_signature(self, tmp_path):
        """Los bytes devueltos tienen la firma de un PNG válido."""
        from telegram_bot import pdf_a_imagen

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(crear_pdf_minimo())

        resultado = pdf_a_imagen(str(pdf_path))

        # PNG signature: 8 bytes \x89PNG\r\n\x1a\n
        assert resultado[:8] == b'\x89PNG\r\n\x1a\n'

    def test_resolucion_mayor_que_72dpi(self, tmp_path):
        """La imagen renderizada a 2x tiene resolución mayor que 72 DPI."""
        from telegram_bot import pdf_a_imagen
        import struct

        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(crear_pdf_minimo())

        resultado = pdf_a_imagen(str(pdf_path))

        # Parsear IHDR de PNG para obtener dimensiones
        # PNG IHDR está en bytes 16-24: width (4), height (4)
        width = struct.unpack('>I', resultado[16:20])[0]
        # A4 a 72 DPI = 595px, a 144 DPI = 1190px
        assert width > 800, f"Ancho {width}px parece demasiado pequeño para 2x"
