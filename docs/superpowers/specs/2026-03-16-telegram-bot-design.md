# Telegram Bot — La Agenda del Finde

**Fecha:** 2026-03-16
**Proyecto:** Scraper Baloncesto Valsequillo
**Estado:** Aprobado

## Objetivo

Enviar automáticamente un mensaje a un grupo de Telegram con el resumen semanal de partidos del CB Valsequillo ("La Agenda del Finde"), incluyendo imagen de la primera página del PDF generado y texto formateado con los partidos.

## Cuándo se envía

Misma lógica que el email existente:
- **Lunes:** siempre (resumen semanal)
- **Cualquier día:** si se detectan cambios en los partidos

## Arquitectura

### Fichero nuevo: `telegram_bot.py`

Fichero independiente, no modifica `scraper_baloncesto.py`. Tres funciones:

1. **`pdf_a_imagen(ruta_pdf) → bytes`**
   Usa `fitz` (PyMuPDF, ya en requirements.txt) para renderizar la primera página del PDF como PNG en memoria. No escribe ficheros temporales.

2. **`formatear_mensaje(partidos_def, partidos_prov, cambios) → str`**
   Construye el texto del mensaje con emojis, fechas, horarios, equipos y pabellón. Si hay cambios detectados, añade sección de aviso.

3. **`enviar_telegram(partidos_def, partidos_prov, cambios=None) → void`**
   Función principal. Lee `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` de variables de entorno. Busca el PDF más reciente (DEFINITIVA primero, PROVISIONAL si no hay). Llama a la API de Telegram:
   - Si hay PDF → `POST /sendPhoto` con la imagen como multipart y el texto como caption
   - Si no hay PDF o falla la imagen → `POST /sendMessage` con solo texto
   - Usa `requests` directamente (sin librería adicional)

### Formato del mensaje

```
🏀 La Agenda del Finde - CB Valsequillo

📅 JORNADA DEFINITIVA:
• Sáb 21/03 - 18:00 | Valsequillo vs Rival | Pabellón X

📅 PROVISIONAL (puede cambiar):
• Dom 22/03 - 11:00 | Otro equipo vs Valsequillo | Pabellón Y

⚠️ CAMBIOS DETECTADOS:
• Partido X: horario cambió de 17:00 a 18:00
```

Si no hay partidos para el finde: mensaje informativo indicando que no hay partidos próximos.

### Integración con GitHub Actions

Nuevo step en `.github/workflows/scraper_automatico.yml`, después del step de email, con la misma condición:

```yaml
- name: Enviar Telegram
  if: success() && steps.should_send_email.outputs.send_email == 'true'
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
| `TELEGRAM_BOT_TOKEN` | Token del bot obtenido desde @BotFather |
| `TELEGRAM_CHAT_ID` | ID del grupo/canal donde se envían los mensajes |

## Comportamiento de fallback

1. Si no existe PDF DEFINITIVA → intenta con PDF PROVISIONAL
2. Si no existe ningún PDF → envía solo mensaje de texto sin imagen
3. Si falla `sendPhoto` → reintenta con `sendMessage` (solo texto)
4. Si falla completamente → escribe el error en `scraper.log` y termina con código de salida 1

## Ficheros modificados

| Fichero | Cambio |
|---------|--------|
| `telegram_bot.py` | **Nuevo** — lógica completa del bot |
| `.github/workflows/scraper_automatico.yml` | Añadir step `Enviar Telegram` |

`scraper_baloncesto.py` no se modifica.
