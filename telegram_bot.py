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
    try:
        page = doc[0]
        matriz = fitz.Matrix(2, 2)
        pixmap = page.get_pixmap(matrix=matriz)
        return pixmap.tobytes("png")
    finally:
        doc.close()


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
