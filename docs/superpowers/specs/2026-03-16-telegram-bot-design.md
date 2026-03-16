# Telegram Bot — La Agenda del Finde

**Fecha:** 2026-03-16
**Proyecto:** Scraper Baloncesto Valsequillo
**Estado:** Borrador

## Objetivo

Enviar automáticamente un mensaje a un grupo de Telegram con el resumen semanal de partidos del CB Valsequillo ("La Agenda del Finde"), incluyendo imagen de la primera página del PDF generado y texto formateado con los partidos.

## Cuándo se envía

Misma lógica que el email existente:
- **Lunes:** siempre (resumen semanal)
- **Cualquier día:** si se detectan cambios en los partidos (detectado vía `scraper.log`)

## Arquitectura

### Fichero nuevo: `telegram_bot.py`

Fichero independiente invocado como `python telegram_bot.py`. No modifica `scraper_baloncesto.py`. Tres funciones:

1. **`pdf_a_imagen(ruta_pdf) → bytes`**
   Usa `fitz` (PyMuPDF, ya en requirements.txt) para renderizar la primera página del PDF como PNG en memoria. Renderiza a 2× escala (`fitz.Matrix(2, 2)`) para obtener ~144 DPI efectivos — calidad suficiente para Telegram. No escribe ficheros temporales.

2. **`formatear_mensaje(partidos, hay_cambios) → str`**
   Construye el texto del mensaje con emojis, fechas, horarios, equipos y pabellón. `partidos` es la lista leída de `partidos_anteriores.json`. `hay_cambios` es booleano — si es `True` añade aviso genérico de cambios detectados (no detalle de cada cambio). El texto se limita a 1024 caracteres (límite de caption de Telegram `sendPhoto`); si supera ese límite, el exceso se omite con "…" al final.

3. **`enviar_telegram() → void`**
   Función principal, sin argumentos — datos tomados de disco y variables de entorno al ejecutarse:
   - Lee `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` de variables de entorno
   - Lee `partidos_anteriores.json` para obtener la lista de partidos actuales
   - Lee `scraper.log` para detectar si hay cambios (busca `"⚠️.*Se detectaron.*cambios"`, mismo patrón que el workflow)
   - Busca el PDF más reciente con el patrón `PARTIDOS_VALSEQUILLO_DEFINITIVA_DD_MM.pdf` (glob: `PARTIDOS_VALSEQUILLO_DEFINITIVA_*.pdf`); si no existe, usa `PARTIDOS_VALSEQUILLO_PROVISIONAL_*.pdf`; si no hay ninguno, omite la imagen
   - Llama a la API de Telegram:
     - Si hay PDF → `POST /sendPhoto` con imagen PNG (multipart) y texto como caption (≤1024 chars)
     - Si no hay PDF o falla `sendPhoto` → `POST /sendMessage` con solo texto
   - Usa `requests` directamente (sin librería `python-telegram-bot`)
   - Si falla completamente → escribe error en `scraper.log` y termina con **exit code 0** (para no bloquear pasos posteriores del workflow)

### Punto de entrada del script

```python
if __name__ == "__main__":
    enviar_telegram()
```

### Formato del mensaje

```
🏀 La Agenda del Finde - CB Valsequillo

📅 JORNADA DEFINITIVA:
• Sáb 21/03 - 18:00 | Valsequillo vs Rival | Pabellón X

📅 PROVISIONAL (puede cambiar):
• Dom 22/03 - 11:00 | Otro equipo vs Valsequillo | Pabellón Y

⚠️ Cambios detectados — revisa el calendario actualizado.
```

Si no hay partidos próximos: `"🏀 CB Valsequillo — No hay partidos próximos programados."`

### Integración con GitHub Actions

Nuevo step en `.github/workflows/scraper_automatico.yml`, después del step de email.

La condición **no usa `success()`** para que Telegram sea independiente del resultado del email (un fallo SMTP no bloquea la notificación de Telegram). El step usa `continue-on-error: true` para que un fallo de Telegram no bloquee los pasos posteriores de commit/push.

```yaml
- name: Enviar Telegram
  if: steps.should_send_email.outputs.send_email == 'true'
  continue-on-error: true
  run: python telegram_bot.py
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

## Dependencias

| Librería | Estado | Uso |
|----------|--------|-----|
| `fitz` (PyMuPDF) | Ya instalada | PDF → PNG |
| `requests` | Ya instalada | Llamadas a API Telegram |

No se añade ninguna dependencia nueva.

## Secrets de GitHub necesarios

| Secret | Descripción |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot obtenido desde @BotFather (formato: `123456:ABC-DEF...`) |
| `TELEGRAM_CHAT_ID` | ID numérico del grupo/canal. **Nota:** los grupos de Telegram tienen ID negativo (ej. `-1001234567890`). No es el nombre del grupo ni el enlace de invitación. |

## Comportamiento de fallback

1. Si no existe PDF DEFINITIVA → intenta con PDF PROVISIONAL
2. Si no existe ningún PDF → envía solo mensaje de texto sin imagen
3. Si falla `sendPhoto` → reintenta con `sendMessage` (solo texto)
4. Si falla completamente → escribe error en `scraper.log` y termina con exit code 0 (el step del workflow tiene `continue-on-error: true` como doble protección)

## Ficheros modificados

| Fichero | Cambio |
|---------|--------|
| `telegram_bot.py` | **Nuevo** — lógica completa del bot |
| `.github/workflows/scraper_automatico.yml` | Añadir step `Enviar Telegram` con `continue-on-error: true` |

`scraper_baloncesto.py` **no se modifica**.
