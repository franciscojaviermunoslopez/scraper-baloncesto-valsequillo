# test_telegram_bot.py
import fitz
import pytest


def crear_pdf_minimo():
    """Crea un PDF mínimo en memoria para tests."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "Test PDF Valsequillo", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


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


# Añadir al final de test_telegram_bot.py

PARTIDOS_EJEMPLO = [
    {
        "dia": "Sábado 21/03/26",
        "hora": "18:00",
        "categoria": "Senior Masc S-A",
        "local": "CB Valsequillo (35008831)",
        "visitante": "Gran Canaria B (35004700)",
        "lugar": "Pab Municipal Valsequillo",
        "origen": "Página 1",
        "jornada_tipo": "DEFINITIVA",
    },
    {
        "dia": "Domingo 22/03/26",
        "hora": "11:00",
        "categoria": "Infantil Masc S-B",
        "local": "Otro Club (35001111)",
        "visitante": "Valsequillo Junior (35008838)",
        "lugar": "IES Valsequillo",
        "origen": "Página 1",
        "jornada_tipo": "PROVISIONAL",
    },
]


class TestFormatearMensaje:
    def test_contiene_header(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=False)
        assert "La Agenda del Finde" in resultado
        assert "CB Valsequillo" in resultado

    def test_partido_definitivo_aparece(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=False)
        assert "DEFINITIVA" in resultado
        assert "Pab Municipal Valsequillo" in resultado

    def test_partido_provisional_aparece(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=False)
        assert "PROVISIONAL" in resultado
        assert "IES Valsequillo" in resultado

    def test_codigos_federativos_eliminados(self):
        """Los códigos (35XXXXXX) no deben aparecer en el mensaje."""
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=False)
        assert "(35008831)" not in resultado
        assert "(35004700)" not in resultado

    def test_sin_cambios_no_aviso(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=False)
        assert "⚠️" not in resultado

    def test_con_cambios_incluye_aviso(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje(PARTIDOS_EJEMPLO, hay_cambios=True)
        assert "⚠️" in resultado
        assert "cambios" in resultado.lower()

    def test_sin_partidos(self):
        from telegram_bot import formatear_mensaje
        resultado = formatear_mensaje([], hay_cambios=False)
        assert "No hay partidos" in resultado

    def test_respeta_limite_1024_chars(self):
        """El mensaje nunca supera 1024 caracteres (límite caption Telegram)."""
        from telegram_bot import formatear_mensaje
        # Generar muchos partidos para forzar truncado
        partidos_largos = PARTIDOS_EJEMPLO * 20
        resultado = formatear_mensaje(partidos_largos, hay_cambios=True)
        assert len(resultado) <= 1024

    def test_truncado_termina_con_puntos_suspensivos(self):
        from telegram_bot import formatear_mensaje
        partidos_largos = PARTIDOS_EJEMPLO * 20
        resultado = formatear_mensaje(partidos_largos, hay_cambios=False)
        assert len(resultado) == 1024
        assert resultado.endswith("…")
