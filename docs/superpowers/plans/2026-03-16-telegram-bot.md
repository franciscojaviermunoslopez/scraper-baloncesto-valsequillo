# Telegram Bot — La Agenda del Finde — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir un bot de Telegram que envíe automáticamente "La Agenda del Finde" (resumen semanal de partidos + imagen del PDF) al grupo de Telegram, con la misma lógica de envío que el email existente (lunes siempre, otros días solo si hay cambios).

**Architecture:** Nuevo fichero `telegram_bot.py` invocado como script independiente desde GitHub Actions. Lee los datos de `partidos_anteriores.json` y `scraper.log` (ya en disco tras ejecutar el scraper), convierte el PDF a PNG con `fitz`, y llama a la API REST de Telegram con `requests`.

**Tech Stack:** Python 3.11, fitz/PyMuPDF (ya instalado), requests (ya instalado), API REST de Telegram (sendPhoto / sendMessage), GitHub Actions secrets.

---

## Ficheros

| Fichero | Acción | Responsabilidad |
|---------|--------|-----------------|
| `telegram_bot.py` | Crear | Lógica completa del bot: conversión PDF→PNG, formateo del mensaje, llamada a la API |
| `test_telegram_bot.py` | Crear | Tests unitarios para las tres funciones (sin llamadas reales a la API) |
| `.github/workflows/scraper_automatico.yml` | Modificar | Añadir step `Enviar Telegram` tras el step de email |

`scraper_baloncesto.py` y `requirements.txt` no se modifican.

---

## Contexto clave del proyecto

**Estructura del JSON** (`partidos_anteriores.json`):
```json
{
  "dia": "Sábado 28/03/26",
  "hora": "18:30",
  "categoria": "Senior Masc S-A",
  "local": "CB Valsequillo (35008831)",
  "visitante": "Gran Canaria B (35004700)",
  "lugar": "Pab Municipal Valsequillo",
  "origen": "Página 1",
  "jornada_tipo": "DEFINITIVA"
}
```
Los nombres de equipos incluyen el código federativo entre paréntesis — hay que eliminarlo al formatear.

**Patrón de archivos PDF:**
- `PARTIDOS_VALSEQUILLO_DEFINITIVA_DD_MM.pdf` → glob: `PARTIDOS_VALSEQUILLO_DEFINITIVA_*.pdf`
- `PARTIDOS_VALSEQUILLO_PROVISIONAL_DD_MM.pdf` → glob: `PARTIDOS_VALSEQUILLO_PROVISIONAL_*.pdf`

**Detección de cambios en log:** buscar la cadena `"⚠️"` y `"Se detectaron"` en `scraper.log`.

**Límite caption Telegram:** 1024 caracteres para `sendPhoto`.

---

## Chunk 1: `pdf_a_imagen` y tests

### Task 1: Test para `pdf_a_imagen`

**Files:**
- Create: `test_telegram_bot.py`

- [ ] **Step 1: Crear el fichero de test con el primer test**

```python
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
```

- [ ] **Step 2: Ejecutar el test para verificar que falla**

```bash
cd /c/Users/fmunoz/Downloads/scraper-baloncesto-valsequillo-main/scraper-baloncesto-valsequillo-main
python -m pytest test_telegram_bot.py::TestPdfAImagen -v
```
Resultado esperado: `ERROR` con `ModuleNotFoundError: No module named 'telegram_bot'`

---

### Task 2: Implementar `pdf_a_imagen`

**Files:**
- Create: `telegram_bot.py`

- [ ] **Step 1: Crear `telegram_bot.py` con la función `pdf_a_imagen`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Telegram para CB Valsequillo — La Agenda del Finde
Envía resumen semanal de partidos al grupo de Telegram.
"""

import glob
import json
import logging
import os
import re
import sys

import fitz  # PyMuPDF
import requests

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def pdf_a_imagen(ruta_pdf: str) -> bytes:
    """
    Renderiza la primera página del PDF como PNG en memoria.
    Usa escala 2x (fitz.Matrix(2,2)) para ~144 DPI efectivos.
    Retorna los bytes PNG. No escribe ficheros temporales.
    """
    doc = fitz.open(ruta_pdf)
    page = doc[0]
    matriz = fitz.Matrix(2, 2)
    pixmap = page.get_pixmap(matrix=matriz)
    return pixmap.tobytes("png")
```

- [ ] **Step 2: Ejecutar los tests de `pdf_a_imagen`**

```bash
python -m pytest test_telegram_bot.py::TestPdfAImagen -v
```
Resultado esperado: `3 passed`

- [ ] **Step 3: Commit**

```bash
git add telegram_bot.py test_telegram_bot.py
git commit -m "feat: add pdf_a_imagen with tests"
```

---

## Chunk 2: `formatear_mensaje` y tests

### Task 3: Tests para `formatear_mensaje`

**Files:**
- Modify: `test_telegram_bot.py`

- [ ] **Step 1: Añadir los tests de `formatear_mensaje` al fichero de test**

```python
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
```

- [ ] **Step 2: Ejecutar los tests para verificar que fallan**

```bash
python -m pytest test_telegram_bot.py::TestFormatearMensaje -v
```
Resultado esperado: todos FAIL con `ImportError` (función no definida aún)

---

### Task 4: Implementar `formatear_mensaje`

**Files:**
- Modify: `telegram_bot.py`

- [ ] **Step 1: Añadir la función `formatear_mensaje` a `telegram_bot.py`**

Añadir después de `pdf_a_imagen`:

```python
_ABREV_DIA = {
    "Lunes": "Lun", "Martes": "Mar", "Miércoles": "Mié",
    "Jueves": "Jue", "Viernes": "Vie", "Sábado": "Sáb", "Domingo": "Dom",
}


def _limpiar_nombre(nombre: str) -> str:
    """Elimina el código federativo entre paréntesis: 'Club (35000000)' → 'Club'."""
    return re.sub(r'\s*\(\d+\)\s*$', '', nombre).strip()


def _formatear_partido(p: dict) -> str:
    """Devuelve una línea formateada para un partido."""
    dia_partes = p["dia"].split()          # ["Sábado", "21/03/26"]
    dia_semana = _ABREV_DIA.get(dia_partes[0], dia_partes[0])
    fecha = dia_partes[1][:5]              # "21/03" (sin año)
    hora = p["hora"]
    local = _limpiar_nombre(p["local"])
    visitante = _limpiar_nombre(p["visitante"])
    lugar = p["lugar"]
    return f"• {dia_semana} {fecha} {hora}h | {local} vs {visitante} | {lugar}"


def formatear_mensaje(partidos: list, hay_cambios: bool) -> str:
    """
    Construye el texto del mensaje de Telegram.
    Respeta el límite de 1024 caracteres (caption de sendPhoto).
    """
    if not partidos:
        return "🏀 CB Valsequillo — No hay partidos próximos programados."

    definitivos = [p for p in partidos if p.get("jornada_tipo") == "DEFINITIVA"]
    provisionales = [p for p in partidos if p.get("jornada_tipo") == "PROVISIONAL"]

    lineas = ["🏀 La Agenda del Finde - CB Valsequillo", ""]

    if definitivos:
        lineas.append("📅 JORNADA DEFINITIVA:")
        for p in definitivos:
            lineas.append(_formatear_partido(p))
        lineas.append("")

    if provisionales:
        lineas.append("📅 PROVISIONAL (puede cambiar):")
        for p in provisionales:
            lineas.append(_formatear_partido(p))
        lineas.append("")

    if hay_cambios:
        lineas.append("⚠️ Cambios detectados — revisa el calendario actualizado.")

    texto = "\n".join(lineas).rstrip()

    if len(texto) > 1024:
        texto = texto[:1023] + "…"

    return texto
```

- [ ] **Step 2: Ejecutar los tests de `formatear_mensaje`**

```bash
python -m pytest test_telegram_bot.py::TestFormatearMensaje -v
```
Resultado esperado: `9 passed`

- [ ] **Step 3: Commit**

```bash
git add telegram_bot.py test_telegram_bot.py
git commit -m "feat: add formatear_mensaje with tests"
```

---

## Chunk 3: `enviar_telegram` y tests

### Task 5: Tests para `enviar_telegram`

**Files:**
- Modify: `test_telegram_bot.py`

- [ ] **Step 1: Añadir los tests de `enviar_telegram` al fichero de test**

```python
# Añadir al final de test_telegram_bot.py
import json
from unittest.mock import MagicMock, patch


class TestEnviarTelegram:
    """Tests de enviar_telegram con mocks — sin llamadas reales a la API."""

    def _env_vars(self):
        return {
            "TELEGRAM_BOT_TOKEN": "123456:TEST-TOKEN",
            "TELEGRAM_CHAT_ID": "-1001234567890",
        }

    def test_envia_foto_cuando_hay_pdf(self, tmp_path, monkeypatch):
        """Cuando existe PDF DEFINITIVA, llama a sendPhoto."""
        from telegram_bot import enviar_telegram

        # Crear partidos.json y PDF de prueba en tmp_path
        partidos = [PARTIDOS_EJEMPLO[0]]
        (tmp_path / "partidos_anteriores.json").write_text(
            json.dumps(partidos), encoding="utf-8"
        )
        pdf_bytes = crear_pdf_minimo()
        pdf_path = tmp_path / "PARTIDOS_VALSEQUILLO_DEFINITIVA_21_03.pdf"
        pdf_path.write_bytes(pdf_bytes)
        (tmp_path / "scraper.log").write_text("", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        with patch("telegram_bot.requests.post", return_value=mock_resp) as mock_post:
            enviar_telegram()

        # Debe haberse llamado a sendPhoto (no sendMessage)
        assert mock_post.called
        call_url = mock_post.call_args[0][0]
        assert "sendPhoto" in call_url

    def test_fallback_a_sendmessage_sin_pdf(self, tmp_path, monkeypatch):
        """Sin PDF, llama a sendMessage en lugar de sendPhoto."""
        from telegram_bot import enviar_telegram

        partidos = [PARTIDOS_EJEMPLO[0]]
        (tmp_path / "partidos_anteriores.json").write_text(
            json.dumps(partidos), encoding="utf-8"
        )
        (tmp_path / "scraper.log").write_text("", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        with patch("telegram_bot.requests.post", return_value=mock_resp) as mock_post:
            enviar_telegram()

        call_url = mock_post.call_args[0][0]
        assert "sendMessage" in call_url

    def test_fallback_sendmessage_si_sendphoto_falla(self, tmp_path, monkeypatch):
        """Si sendPhoto falla (status != 200), reintenta con sendMessage."""
        from telegram_bot import enviar_telegram

        partidos = [PARTIDOS_EJEMPLO[0]]
        (tmp_path / "partidos_anteriores.json").write_text(
            json.dumps(partidos), encoding="utf-8"
        )
        pdf_path = tmp_path / "PARTIDOS_VALSEQUILLO_DEFINITIVA_21_03.pdf"
        pdf_path.write_bytes(crear_pdf_minimo())
        (tmp_path / "scraper.log").write_text("", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")

        resp_fallo = MagicMock()
        resp_fallo.status_code = 400
        resp_fallo.json.return_value = {"ok": False, "description": "Bad Request"}

        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.json.return_value = {"ok": True}

        with patch("telegram_bot.requests.post", side_effect=[resp_fallo, resp_ok]) as mock_post:
            enviar_telegram()

        assert mock_post.call_count == 2
        assert "sendPhoto" in mock_post.call_args_list[0][0][0]
        assert "sendMessage" in mock_post.call_args_list[1][0][0]

    def test_detecta_cambios_en_log(self, tmp_path, monkeypatch):
        """Si scraper.log contiene el aviso de cambios, el mensaje incluye ⚠️."""
        from telegram_bot import enviar_telegram

        partidos = [PARTIDOS_EJEMPLO[0]]
        (tmp_path / "partidos_anteriores.json").write_text(
            json.dumps(partidos), encoding="utf-8"
        )
        (tmp_path / "scraper.log").write_text(
            "2026-03-16 - WARNING - ⚠️ Se detectaron 2 cambios en partidos!",
            encoding="utf-8",
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        texto_enviado = None

        def capturar_post(url, **kwargs):
            nonlocal texto_enviado
            data = kwargs.get("data", {})
            texto_enviado = data.get("caption") or data.get("text", "")
            return mock_resp

        with patch("telegram_bot.requests.post", side_effect=capturar_post):
            enviar_telegram()

        assert texto_enviado is not None
        assert "⚠️" in texto_enviado

    def test_no_lanza_excepcion_si_falla_completamente(self, tmp_path, monkeypatch):
        """Si todo falla, la función no lanza excepción (el workflow no se bloquea)."""
        from telegram_bot import enviar_telegram

        partidos = [PARTIDOS_EJEMPLO[0]]
        (tmp_path / "partidos_anteriores.json").write_text(
            json.dumps(partidos), encoding="utf-8"
        )
        (tmp_path / "scraper.log").write_text("", encoding="utf-8")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:TEST")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123")

        with patch("telegram_bot.requests.post", side_effect=Exception("Network error")):
            enviar_telegram()  # No debe lanzar — si lanza, el test falla
```

- [ ] **Step 2: Ejecutar los tests para verificar que fallan**

```bash
python -m pytest test_telegram_bot.py::TestEnviarTelegram -v
```
Resultado esperado: todos FAIL con `ImportError` (función no definida aún)

---

### Task 6: Implementar `enviar_telegram`

**Files:**
- Modify: `telegram_bot.py`

- [ ] **Step 1: Añadir `enviar_telegram` y el bloque `__main__` a `telegram_bot.py`**

Añadir al final del fichero:

```python
def _detectar_cambios_en_log(ruta_log: str = "scraper.log") -> bool:
    """Retorna True si scraper.log contiene el aviso de cambios detectados."""
    try:
        with open(ruta_log, encoding="utf-8") as f:
            contenido = f.read()
        return bool(re.search(r"⚠️.*Se detectaron.*cambios", contenido))
    except FileNotFoundError:
        return False


def _buscar_pdf() -> str | None:
    """
    Busca el PDF más reciente en el directorio actual.
    Prioridad: DEFINITIVA → PROVISIONAL → None.
    """
    for patron in [
        "PARTIDOS_VALSEQUILLO_DEFINITIVA_*.pdf",
        "PARTIDOS_VALSEQUILLO_PROVISIONAL_*.pdf",
    ]:
        archivos = sorted(glob.glob(patron))
        if archivos:
            return archivos[-1]
    return None


def _llamar_send_photo(token: str, chat_id: str, imagen_bytes: bytes, texto: str) -> bool:
    """Intenta enviar imagen + caption. Retorna True si tuvo éxito."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    respuesta = requests.post(
        url,
        data={"chat_id": chat_id, "caption": texto, "parse_mode": "HTML"},
        files={"photo": ("agenda.png", imagen_bytes, "image/png")},
        timeout=30,
    )
    resultado = respuesta.json()
    if respuesta.status_code == 200 and resultado.get("ok"):
        logging.info("✅ Telegram: imagen enviada correctamente")
        return True
    logging.warning(f"⚠️ Telegram sendPhoto falló: {resultado.get('description')}")
    return False


def _llamar_send_message(token: str, chat_id: str, texto: str) -> bool:
    """Envía mensaje de texto. Retorna True si tuvo éxito."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    respuesta = requests.post(
        url,
        data={"chat_id": chat_id, "text": texto, "parse_mode": "HTML"},
        timeout=30,
    )
    resultado = respuesta.json()
    if respuesta.status_code == 200 and resultado.get("ok"):
        logging.info("✅ Telegram: mensaje de texto enviado correctamente")
        return True
    logging.warning(f"⚠️ Telegram sendMessage falló: {resultado.get('description')}")
    return False


def enviar_telegram() -> None:
    """
    Función principal. Lee datos de disco y variables de entorno.
    Envía imagen+texto (o solo texto) al grupo de Telegram.
    Nunca lanza excepciones — los errores se registran en scraper.log.
    """
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            logging.error("❌ Telegram: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
            return

        # Leer partidos desde disco
        try:
            with open("partidos_anteriores.json", encoding="utf-8") as f:
                partidos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"❌ Telegram: no se pudo leer partidos_anteriores.json — {e}")
            partidos = []

        hay_cambios = _detectar_cambios_en_log()
        texto = formatear_mensaje(partidos, hay_cambios)

        # Intentar enviar con imagen
        ruta_pdf = _buscar_pdf()
        if ruta_pdf:
            try:
                imagen = pdf_a_imagen(ruta_pdf)
                if _llamar_send_photo(token, chat_id, imagen, texto):
                    return
            except Exception as e:
                logging.warning(f"⚠️ Telegram: error generando imagen — {e}")

        # Fallback: solo texto
        _llamar_send_message(token, chat_id, texto)

    except Exception as e:
        logging.error(f"❌ Telegram: error inesperado — {e}")


if __name__ == "__main__":
    enviar_telegram()
```

- [ ] **Step 2: Ejecutar todos los tests**

```bash
python -m pytest test_telegram_bot.py -v
```
Resultado esperado: todos los tests `PASSED` (3 + 9 + 5 = 17 en total)

- [ ] **Step 3: Commit**

```bash
git add telegram_bot.py test_telegram_bot.py
git commit -m "feat: add enviar_telegram with tests"
```

---

## Chunk 4: Integración GitHub Actions

### Task 7: Añadir step `Enviar Telegram` al workflow

**Files:**
- Modify: `.github/workflows/scraper_automatico.yml`

- [ ] **Step 1: Localizar el paso de email en el workflow**

Abrir `.github/workflows/scraper_automatico.yml` y localizar el step `Enviar email con PDF adjunto` (línea ~87). El nuevo step va **inmediatamente después** del cierre de ese bloque (después de la línea `PARTIDOS_VALSEQUILLO_*.ics`).

- [ ] **Step 2: Insertar el nuevo step**

Añadir después del step de email (tras la línea que cierra `attachments:`):

```yaml
    - name: Enviar Telegram
      if: steps.should_send_email.outputs.send_email == 'true'
      continue-on-error: true
      run: python telegram_bot.py
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

**Notas importantes:**
- La condición **no incluye `success()`** — Telegram es independiente del éxito del email.
- `continue-on-error: true` — un fallo de Telegram no bloquea los commits posteriores.

- [ ] **Step 3: Verificar el YAML es sintácticamente correcto**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/scraper_automatico.yml')); print('YAML OK')"
```
Resultado esperado: `YAML OK`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/scraper_automatico.yml
git commit -m "feat: add Telegram notification step to GitHub Actions workflow"
```

---

## Configuración manual (fuera del código)

Tras el despliegue, el usuario debe completar estos pasos una sola vez:

1. **Crear el bot en Telegram:**
   - Hablar con `@BotFather` en Telegram → `/newbot` → seguir instrucciones
   - Copiar el token (formato `123456:ABC-DEF...`)

2. **Obtener el Chat ID del grupo:**
   - Añadir el bot al grupo de padres
   - Acceder a `https://api.telegram.org/bot<TOKEN>/getUpdates` desde el navegador
   - Buscar `"chat": {"id": -XXXXXXXXXX, ...}` — ese número negativo es el `TELEGRAM_CHAT_ID`

3. **Añadir los secrets en GitHub:**
   - Repositorio → Settings → Secrets and variables → Actions → New repository secret
   - `TELEGRAM_BOT_TOKEN` = token del paso 1
   - `TELEGRAM_CHAT_ID` = ID negativo del paso 2

---

## Verificación final

- [ ] Ejecutar todos los tests: `python -m pytest test_telegram_bot.py -v`
- [ ] Confirmar que los 17 tests pasan sin errores
- [ ] Revisar el YAML del workflow: `python -c "import yaml; yaml.safe_load(open('.github/workflows/scraper_automatico.yml')); print('YAML OK')"`
- [ ] Confirmar que `scraper_baloncesto.py` y `requirements.txt` **no fueron modificados**
